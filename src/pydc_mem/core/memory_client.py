# user_attribute_client.py
# Python 3.12
#
# Usage:
#   from user_attribute_client import UserAttributeClient, MemoryCandidate
#   client = UserAttributeClient(base_url="https://api.example.com", auth_token="bearer-xyz")
#   candidates = [
#       MemoryCandidate(entity="Alex", attribute="preferred_airline", value="Delta Airlines"),
#       MemoryCandidate(entity="Alex", attribute="seat_preference", value="window"),
#   ]
#   report = client.upsert_from_candidates(user_id="alex-id-123", candidates=candidates)
#   print(report)

"""
needs the following env vars:

MEMORY_DLO
MEMORY_CONNECTOR
VECTOR_IDX_DLM
CHUNK_DLM
SALESFORCE_ORGANIZATION_ID
"""

from __future__ import annotations

import os
import pdb
from datetime import datetime
from dataclasses import dataclass, field
from typing import Iterable, List, Dict, Any, Optional, Tuple, Literal

import httpx
from uuid6 import uuid7
from dotenv import load_dotenv
from openai import OpenAI

from .memory_extractor import MemoryCandidate
from pydc_mem.util.ingestion_client import DataCloudIngestionClient
from pydc_mem.util.query_svc import QueryServiceClient
from pydc_mem.util.memory_results_parser import parse_tabular_payload

DEFAULT_MODEL = "gpt-4o"

# --- Result/Report types -------------------------------------------------------
@dataclass
class UpsertItemResult:
    attribute: str
    old_value: Optional[str]
    new_value: str
    action: str  # "added" | "updated" | "skipped"
    status_code: Optional[int] = None
    error: Optional[str] = None


@dataclass
class UpsertReport:
    user_id: str
    added: int = 0
    updated: int = 0
    skipped: int = 0
    errors: int = 0
    details: List[UpsertItemResult] = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f"UpsertReport(user_id={self.user_id}, "
            f"added={self.added}, updated={self.updated}, skipped={self.skipped}, errors={self.errors})"
        )


# --- Client -------------------------------------------------------------------
class UserAttributeClient:
    """
    Minimal client for a 'user_attributes' REST service. It only does:
    - read all attributes for a user
    - add new attribute rows
    - update existing attribute rows
    - choose Add vs Update vs Noop based on MemoryCandidate list
    - DOES NOT delete

    Assumed REST contract (override endpoints if needed):
      GET  {base_url}/user_attributes?user_id={user_id}
      POST {base_url}/user_attributes
      PUT  {base_url}/user_attributes/{user_id}/{attribute}

    You can customize paths via constructor.
    """

    def __init__(
        self
    ) -> None:
        load_dotenv()

        self.dlo = os.getenv('MEMORY_DLO')
        self.connector = os.getenv('MEMORY_CONNECTOR')
        self.vector_index_dlm = os.getenv("VECTOR_IDX_DLM")
        self.chunk_dlm = os.getenv("CHUNK_DLM")
        self.tenantId = os.getenv('SALESFORCE_ORGANIZATION_ID')
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.llm_client = OpenAI(api_key=self.api_key)
        self.query_svc_client = QueryServiceClient()
        self.ingestion_client = DataCloudIngestionClient()

    # -------------------- public API --------------------
    def fetch_relevant_attributes(self, user_id: str, utterance: str) -> List[Dict]:
        resp = self._search_relevant_memories(user_id=user_id, utterance=utterance)
        if resp is None:
            return []
        try:
            return parse_tabular_payload(resp.json())["rows"]
        except Exception:
            return []

    def fetch_user_attributes(self, user_id: str) -> List[Dict]:
        resp = self._search_all_memories(user_id=user_id)
        if resp is None:
            return []
        try:
            return parse_tabular_payload(resp.json())["rows"]
        except Exception:
            return []
    def fetch_relevant_attributes_with_src(self, user_id: str, utterance: str) -> List[Dict]:
        resp = self._search_relevant_attributes_with_src(user_id=user_id, utterance=utterance)
        if resp is None:
            return []
        try:
            return parse_tabular_payload(resp.json())["rows"]
        except Exception:
            return []

    def upsert_from_candidates(
        self,
        user_id: str,
        candidates: List[MemoryCandidate],
        *,
        normalize_attributes: bool = True,
        case_insensitive_compare: bool = True,
        dedupe_last_write_wins: bool = True,
    ) -> UpsertReport:
        """
        Given MemoryCandidate objects for a user, add/update attributes accordingly:
        - If attribute missing -> POST (Add)
        - If attribute present with the same value -> Noop (Skip)
        - If attribute present with a different value -> PUT (Update)
        - Never deletes.
        """
        report = UpsertReport(user_id=user_id)

        # # Fetch current state
        # current_mems = self.fetch_user_attributes(user_id)

        # Optional dedupe: last candidate per attribute wins
        if dedupe_last_write_wins:
            combined: Dict[str, MemoryCandidate] = {}
            for c in candidates:
                key = self._norm(c.attribute) if normalize_attributes else c.attribute
                combined[key] = c
            work_list = list(combined.values())
        else:
            work_list = candidates

        for c in work_list:
            attr_key = self._norm(c.attribute) if normalize_attributes else c.attribute
            current_mems = self.fetch_relevant_attributes_with_src(user_id=user_id, utterance=attr_key)
            new_value = c.value.strip()
            old_value = None
            current = {}

            if len(current_mems) > 0:
                results = self._filter_eq(current_mems, "attribute__c", attr_key)
                current = results[0] if len(results) > 0 else {}
                old_value = current.get("value__c") if current else None

            # Compare values (optionally case-insensitive)
            if old_value is not None and self._equal(old_value, new_value, case_insensitive_compare):
                report.skipped += 1
                report.details.append(
                    UpsertItemResult(attribute=attr_key, old_value=old_value, new_value=new_value, action="skipped")
                )
                continue

            if old_value is None:
                # Add (POST)
                status, err = self._create_attribute(user_id, attr_key, new_value)
                if 200 <= (status or 0) < 300:
                    report.added += 1
                    report.details.append(
                        UpsertItemResult(attribute=attr_key, old_value=None, new_value=new_value, action="added", status_code=status)
                    )
                    current[attr_key] = new_value
                else:
                    report.errors += 1
                    report.details.append(
                        UpsertItemResult(attribute=attr_key, old_value=None, new_value=new_value, action="added", status_code=status, error=err)
                    )
            else:
                # Update (PUT)
                current['value__c'] = new_value
                update_obj = {
                    "id": current['id__c'],
                    "value__c": new_value,
                    "lastModifiedAt__c": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                status, err = self._update_attribute(update_obj)
                if 200 <= (status or 0) < 300:
                    report.updated += 1
                    report.details.append(
                        UpsertItemResult(attribute=attr_key, old_value=old_value, new_value=new_value, action="updated", status_code=status)
                    )
                else:
                    report.errors += 1
                    report.details.append(
                        UpsertItemResult(attribute=attr_key, old_value=old_value, new_value=new_value, action="updated", status_code=status, error=err)
                    )
        return report


    def _filter_eq(self, rows: Iterable[Dict[str, Any]], field: str, value: Any, *, case_sensitive: bool = False) -> List[
        Dict[str, Any]]:
        """
        Return rows where row[field] == value.
        - Strings are case-insensitive by default (set case_sensitive=True to change).
        - Missing fields are treated as None.
        """
        def norm(x):
            return x if (case_sensitive or not isinstance(x, str)) else x.casefold()

        target = norm(value)
        out = []
        for row in rows:
            v = row.get(field)
            if self._llm_compare_strings(norm(v), target):
                out.append(row)
        return out

    # -------------------- HTTP helpers --------------------
    def _create_attribute(self, user_id: str, attribute: str, value: str) -> Tuple[Optional[int], Optional[str]]:
        data = [{
            "id": str(uuid7()),
            "userId": user_id,
            "tenantId": self.tenantId,
            "attribute": attribute,
            "value": value,
            "createdAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updatedBy": "system",
            "source": "experimentation",
            "lastModifiedAt__c": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }]
        request_object = {"data": data}
        response = self.ingestion_client.ingest_data(request_object, self.connector, self.dlo)
        return self._status_err(response)

    def _update_attribute(self, update_obj) -> Tuple[Optional[int], Optional[str]]:
        data = [update_obj]
        request_object = {"data": data}
        response = self.ingestion_client.ingest_data(request_object, self.connector, self.dlo)
        return self._status_err(response)

    def _search_all_memories(self, user_id: str, **kwargs) -> Optional[httpx.Response]:
        """
        Fetches all current memories of a user
        """
        sql = f"""
            SELECT
                *
            FROM
                "{self.dlo}__dlm"
            WHERE
                "userId__c" = '{user_id}'    
            """
        request_obj = {
            "sql": sql
        }
        response = self.query_svc_client.read_data(request_obj)
        return response

    def _search_relevant_memories(self, user_id: str, utterance: str, limit=1,  **kwargs):
        """
        fetches memories/attributes relevant to given utterance
        """
        sql = f"""
         SELECT
            index.RecordId__c,
            index.score__c,
            chunk.Chunk__c 
         FROM 
            vector_search(TABLE({self.vector_index_dlm}), '{utterance}', '', {limit}) AS index 
         JOIN 
            {self.chunk_dlm} AS chunk
         ON 
            index.RecordId__c = chunk.RecordId__c
        """
        request_obj = {
            "sql": sql
        }
        response = self.query_svc_client.read_data(request_obj)
        return response

    def _search_relevant_attributes_with_src(self, user_id: str, utterance: str, limit=1, **kwargs):
        """
        fetches memories/attributes relevant to given utterance
        """
        sql = f"""
         SELECT
            source.*
         FROM 
            vector_search(TABLE({self.vector_index_dlm}), '{utterance}', '', {limit}) AS index 
         JOIN 
            {self.chunk_dlm} AS chunk
         ON 
            index.RecordId__c = chunk.RecordId__c
         JOIN
            {self.dlo}__dlm AS source
         ON 
            chunk.SourceRecordId__c = source.Id__c   
        """
        request_obj = {
            "sql": sql
        }
        response = self.query_svc_client.read_data(request_obj)
        return response

    def _llm_compare_strings(
            self,
            src: str,
            dest: str,
            model: str = DEFAULT_MODEL,
            temperature: float = 0.0,
            comparison_type: Literal["exact", "semantic", "fuzzy"] = "semantic",
            fallback_to_simple: bool = True
    ) -> bool:
        """
        Use an LLM to compare two strings for equality and return a boolean result.

        Args:
            src: First string to compare
            dest: Second string to compare
            model: OpenAI model to use
            temperature: Temperature for the LLM (0.0 for deterministic results)
            comparison_type: Type of comparison to perform
                - "exact": Exact string match (case-insensitive)
                - "semantic": Semantic similarity (same meaning)
                - "fuzzy": Fuzzy matching (handles typos, abbreviations)
            fallback_to_simple: Whether to fallback to simple comparison on error

        Returns:
            bool: True if strings are equal, False otherwise
        """
        if not src or not dest:
            return src == dest

        # Define comparison instructions based on type
        comparison_instructions = {
            "exact": "Compare for exact equality (ignoring case and whitespace).",
            "semantic": "Compare for semantic equality (same meaning, even if worded differently).",
            "fuzzy": "Compare for fuzzy equality (handle typos, abbreviations, and variations)."
        }

        prompt = f"""Compare these two strings for meaning only (real-world or user-facing meaning). Ignore code, syntax, or naming differences: String 1: "{src}" String 2: "{dest}". {comparison_instructions[comparison_type]}. Respond with ONLY "TRUE" or "FALSE" - no other text, no explanation, no punctuation."""

        try:
            response = self.llm_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system",
                     "content": "You are a precise string comparison tool. Always respond with only TRUE or FALSE."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=10
            )

            result = response.choices[0].message.content.strip().upper()
            # Validate response
            if result not in ["TRUE", "FALSE"]:
                if fallback_to_simple:
                    return src.strip().lower() == dest.strip().lower()
                raise ValueError(f"Invalid LLM response: {result}")

            return result == "TRUE"
        except Exception as e:
            if fallback_to_simple:
                print(f"LLM comparison failed: {e}. Falling back to simple comparison.")
                return src.strip().lower() == dest.strip().lower()
            raise e

    @staticmethod
    def _status_err(resp: Optional[httpx.Response]) -> Tuple[Optional[int], Optional[str]]:
        if resp is None:
            return None, "request failed (no response)"
        if 200 <= resp.status_code < 300:
            return resp.status_code, None
        try:
            payload = resp.json()
            err = payload.get("error") if isinstance(payload, dict) else payload
        except Exception:
            err = resp.text
        return resp.status_code, str(err)

    @staticmethod
    def _norm(attr: str) -> str:
        return attr.strip().lower().replace(" ", "_")

    @staticmethod
    def _equal(a: str, b: str, case_insensitive: bool) -> bool:
        return (a.strip().lower() == b.strip().lower()) if case_insensitive else (a.strip() == b.strip())
