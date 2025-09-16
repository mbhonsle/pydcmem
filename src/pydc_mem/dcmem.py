# memory_pipeline_adapter.py
# Python 3.12
#
# Purpose:
#   Glue code that:
#     1) calls the LLM via MemoryExtractor to get memory candidates
#     2) upserts them into the user_attributes table via UserAttributeClient
#
# Usage (script):
#   export OPENAI_API_KEY=sk-...
#   python memory_pipeline_adapter.py --api-base https://api.example.com \
#     --user-id alex-id-123 \
#     --utterance "I usually fly Delta and prefer window seats."
#
# Usage (embedded):
#   from memory_extractor import MemoryExtractor
#   from user_attribute_client import UserAttributeClient
#   from memory_pipeline_adapter import AgentMemoryOrchestrator
#
#   extractor = MemoryExtractor()
#   ua_client = UserAttributeClient(base_url="https://api.example.com", auth_token="bearer-xyz")
#   orch = AgentMemoryOrchestrator(extractor, ua_client)
#   candidates, report = orch.process(
#       user_id="alex-id-123",
#       utterance="I usually fly Delta and prefer window seats.",
#       session_vars={"passengers": 2, "class": "economy"},
#       recent_dialogue=[("Agent", "Do you want Delta again?"), ("User", "Yes, Delta")],
#       past_memory_facts=["Home airport = SFO"],
#   )
#   print(report)
#   for d in report.details:
#       print(d.attribute, d.action, "->", d.new_value)

from __future__ import annotations

import argparse
import json
from typing import Any, Iterable, List, Optional, Sequence, Tuple

# These imports assume the previous files are available alongside this module.
from core.memory_client import UserAttributeClient, UpsertReport
from core.memory_extractor import MemoryExtractor, MemoryCandidate

class AgentMemoryOrchestrator:
    """
    Orchestrates end-to-end:
      - LLM extraction of memory candidates (MemoryExtractor)
      - Upsert to user_attributes via REST (UserAttributeClient)

    Returns both the candidates and the upsert report for observability.
    """

    def __init__(self, extractor: MemoryExtractor, ua_client: UserAttributeClient) -> None:
        self.extractor = extractor
        self.ua_client = ua_client

    def update(self, *, user_id: str, utterance: str, session_vars: Optional[dict[str, Any]] = None,
               recent_dialogue: Optional[Sequence[Tuple[str, str]] | Sequence[str]] = None,
               past_memory_facts: Optional[Iterable[str]] = None, dry_run: bool = False) -> tuple[List[MemoryCandidate], Optional[UpsertReport]]:
        """
        1) Extract memory candidates from the utterance (+ optional context).
        2) If not dry_run, upsert them into user_attributes for the given user_id.
        Returns (candidates, report). Report is None in dry_run mode.
        """
        candidates = self.extractor.extract(
            utterance=utterance,
            session_vars=session_vars,
            recent_dialogue=recent_dialogue,
            past_memory_facts=past_memory_facts,
        )

        if dry_run:
            return candidates, None

        report = self.ua_client.upsert_from_candidates(
            user_id=user_id,
            candidates=candidates,
            # tune these knobs as you like:
            normalize_attributes=True,
            case_insensitive_compare=True,
            dedupe_last_write_wins=True,
        )
        return candidates, report

    def get(self, user_id: str, utterance: str):
        self.ua_client.fetch_relevant_attributes(user_id=user_id, utterance=utterance)


# ---------------- CLI for convenience/testing ----------------

def _build_cli() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="End-to-end memory extraction → user_attributes upsert.")
    p.add_argument("--user-id", required=True, help="The canonical user_id for user_attributes")
    p.add_argument("--utterance", required=True, help="The user's latest message to extract from")
    p.add_argument("--op-type", required=True, default="update", help="Type of Memory Op: update, get")
    p.add_argument("--dry-run", action="store_true", help="Only extract; do not call REST to upsert")
    p.add_argument("--json", action="store_true", help="Print candidates as JSON")
    return p


def _main() -> None:
    args = _build_cli().parse_args()

    # 1) Build dependencies
    extractor = MemoryExtractor()  # reads OPENAI_API_KEY from env
    ua_client = UserAttributeClient()

    # 2) Orchestrate
    orch = AgentMemoryOrchestrator(extractor, ua_client)
    if args.op_type == 'update':
        handle_update(args, orch)
    elif args.op_type == 'get':
        handle_get(args, orch)

def handle_get(args, orch):
    orch.get(user_id=args.user_id, utterance=args.utterance)

def handle_update(args, orch):
    candidates, report = orch.update(user_id=args.user_id, utterance=args.utterance, session_vars=None,
                                     recent_dialogue=None, past_memory_facts=None, dry_run=args.dry_run)
    # 3) Print results
    if args.json:
        print(json.dumps([c.model_dump() for c in candidates], ensure_ascii=False, indent=2))
    else:
        for c in candidates:
            print(f"- {c.entity}: {c.attribute} = {c.value}")
    if report:
        print("\n", report)
        for d in report.details:
            print(f"  {d.attribute}: {d.action} ({d.old_value!r} -> {d.new_value!r})"
                  f"{'' if d.error is None else ' ERROR=' + d.error}")


if __name__ == "__main__":
    _main()