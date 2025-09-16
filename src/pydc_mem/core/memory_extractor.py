# memory_extractor.py
# Python 3.12
#
# Usage (from another script):
#   from memory_extractor import MemoryExtractor
#   extractor = MemoryExtractor()  # OPENAI_API_KEY from env
#   results = extractor.extract("I usually fly Delta and prefer window seats.")
#   for mc in results:
#       print(mc.attribute, "=>", mc.value)

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from openai import OpenAI
from pydantic import BaseModel, ConfigDict, field_validator
from dotenv import load_dotenv


class MemoryCandidate(BaseModel):
    """
    Single memory fact extracted for long-term storage.
    """
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    entity: str
    attribute: str
    value: str

    @field_validator("entity", "attribute", "value")
    @classmethod
    def _not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("must be non-empty")
        return v


class MemoryExtractor:
    """
    Calls an OpenAI LLM to extract memory-worthy facts from a snippet of conversation.
    Returns validated Pydantic models (MemoryCandidate).

    - Reads OPENAI_API_KEY from the environment by default.
    - You can override the model, system instructions, and the user template.
    """

    DEFAULT_MODEL = "gpt-4o-mini"

    DEFAULT_SYSTEM = """\
You are an AI assistant that extracts long-term, user-specific memory facts from a short conversation snippet.
Your job is to identify facts that should persist across sessions (e.g., preferences, stable attributes, recurring behaviors).
Do NOT include transient details (one-off dates/times, temporary search results, ephemeral steps).
Return ONLY a JSON array of objects, where each object has exactly these keys:
  - "entity": the user name or identifier (use "User" if unknown)
  - "attribute": the canonical attribute name (e.g., "preferred_airline", "seat_preference")
  - "value": the attribute value as a short string

Examples:
[
  {"entity": "Alex", "attribute": "preferred_airline", "value": "Delta Airlines"},
  {"entity": "Alex", "attribute": "seat_preference", "value": "window"}
]
"""

    DEFAULT_USER_TEMPLATE = """\
Context
-------
Session Variables:
{session_vars}

Recent Dialogue:
{recent_dialogue}

Past Memory Facts:
{past_memory_facts}

Instruction
-----------
Given the above, extract memory-worthy facts from the user's latest message:
"{utterance}"

Output ONLY a JSON array of objects with keys "entity", "attribute", and "value".
If there are no memory-worthy facts, return [].
"""

    _JSON_ARRAY_REGEX = re.compile(
        r"\[\s*(?:\{.*?\}\s*,\s*)*\{.*?\}\s*\]", flags=re.DOTALL
    )

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        model: str = DEFAULT_MODEL,
        system_instructions: str = DEFAULT_SYSTEM,
        user_template: str = DEFAULT_USER_TEMPLATE,
        client: Optional[OpenAI] = None,
        temperature: float = 0.0,
        max_tokens: int = 300,
    ) -> None:
        load_dotenv()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key and client is None:
            raise RuntimeError("OPENAI_API_KEY is not set and no OpenAI client was provided.")
        self.client = client or OpenAI(api_key=self.api_key)
        self.model = model
        self.system_instructions = system_instructions
        self.user_template = user_template
        self.temperature = temperature
        self.max_tokens = max_tokens

    # ---------------------------
    # Public API
    # ---------------------------
    def extract(
        self,
        utterance: str,
        *,
        session_vars: Optional[Dict[str, Any]] = None,
        recent_dialogue: Optional[Sequence[Tuple[str, str]] | Sequence[str]] = None,
        past_memory_facts: Optional[Iterable[str]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> List[MemoryCandidate]:
        """
        Extracts memory candidates as Pydantic models.

        - utterance: the user's latest message (required)
        - session_vars: dict of short-lived session variables (optional)
        - recent_dialogue: list of (speaker, text) tuples or plain strings (optional)
        - past_memory_facts: iterable of strings; previously known facts to show the LLM (optional)
        """
        raw = self._call_llm(
            utterance=utterance,
            session_vars=session_vars,
            recent_dialogue=recent_dialogue,
            past_memory_facts=past_memory_facts,
            model=model or self.model,
            temperature=self._pick(temperature, self.temperature),
            max_tokens=self._pick(max_tokens, self.max_tokens),
        )
        data = self._parse_json_array(raw)
        return self._to_pydantic_list(data)

    def extract_dicts(
        self,
        utterance: str,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """
        Same as `extract`, but returns a list of dicts (useful if you don't want Pydantic objects).
        """
        raw = self._call_llm(utterance=utterance, **kwargs)
        return self._parse_json_array(raw)

    def extract_json(
        self,
        utterance: str,
        **kwargs: Any,
    ) -> str:
        """
        Same as `extract`, but returns a pretty-printed JSON string.
        """
        rows = self.extract_dicts(utterance, **kwargs)
        return json.dumps(rows, ensure_ascii=False, indent=2)

    # ---------------------------
    # Internals
    # ---------------------------
    def _call_llm(
        self,
        *,
        utterance: str,
        session_vars: Optional[Dict[str, Any]] = None,
        recent_dialogue: Optional[Sequence[Tuple[str, str]] | Sequence[str]] = None,
        past_memory_facts: Optional[Iterable[str]] = None,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        messages = [
            {"role": "system", "content": self.system_instructions},
            {
                "role": "user",
                "content": self._render_user_prompt(
                    utterance=utterance,
                    session_vars=session_vars,
                    recent_dialogue=recent_dialogue,
                    past_memory_facts=past_memory_facts,
                ),
            },
        ]

        resp = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return (resp.choices[0].message.content or "").strip()

    def _render_user_prompt(
        self,
        *,
        utterance: str,
        session_vars: Optional[Dict[str, Any]],
        recent_dialogue: Optional[Sequence[Tuple[str, str]] | Sequence[str]],
        past_memory_facts: Optional[Iterable[str]],
    ) -> str:
        sv = " ".join(f"{k}={v}" for k, v in (session_vars or {}).items()) or "(none)"
        rd = self._format_dialogue(recent_dialogue) or "(none)"
        pmf = self._format_bullets(past_memory_facts) or "(none)"

        return self.user_template.format(
            session_vars=sv,
            recent_dialogue=rd,
            past_memory_facts=pmf,
            utterance=utterance.strip(),
        )

    @staticmethod
    def _format_dialogue(
        dialogue: Optional[Sequence[Tuple[str, str]] | Sequence[str]]
    ) -> str:
        if not dialogue:
            return ""
        lines: List[str] = []
        # Accept either list[str] or list[tuple[str, str]]
        if dialogue and isinstance(dialogue[0], tuple):
            for speaker, text in dialogue:  # type: ignore[index]
                lines.append(f"{speaker}: {text}")
        else:
            for text in dialogue:  # type: ignore[assignment]
                lines.append(str(text))
        return "\n".join(lines)

    @staticmethod
    def _format_bullets(items: Optional[Iterable[str]]) -> str:
        if not items:
            return ""
        return "\n".join(f"- {it}" for it in items)

    @classmethod
    def _parse_json_array(cls, maybe_json: str) -> List[Dict[str, Any]]:
        # Try direct parse
        try:
            parsed = json.loads(maybe_json)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass
        # Fallback: regex to pluck the first JSON array
        m = cls._JSON_ARRAY_REGEX.search(maybe_json)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
        return []

    @staticmethod
    def _to_pydantic_list(rows: List[Dict[str, Any]]) -> List[MemoryCandidate]:
        out: List[MemoryCandidate] = []
        for row in rows:
            try:
                out.append(MemoryCandidate.model_validate(row))
            except Exception:
                # Silently skip invalid rows; callers can add logging if desired.
                continue
        return out

    @staticmethod
    def _pick(v: Optional[Any], default: Any) -> Any:
        return default if v is None else v