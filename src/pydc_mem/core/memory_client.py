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
from typing import Iterable, List, Dict, Any, Optional, Tuple

import httpx
from uuid6 import uuid7
from dotenv import load_dotenv

from .memory_extractor import MemoryCandidate
from util.ingestion_client import DataCloudIngestionClient
from util.query_svc import QueryServiceClient
from util.memory_results_parser import parse_tabular_payload


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
        self.query_svc_client = QueryServiceClient()
        self.ingestion_client = DataCloudIngestionClient()

    # -------------------- public API --------------------
    def fetch_relevant_attributes(self, user_id: str, utterance: str) -> List[Dict]:
        resp = self._search_relevant_memories(user_id=user_id, utterance=utterance)
        print(resp.json())
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

        # Fetch current state
        current_mems = self.fetch_user_attributes(user_id)

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
            new_value = c.value.strip()
            old_value = None
            current = {}
            if len(current_mems) > 0:
                current = self._filter_eq(current_mems, "attribute__c", attr_key)[0]
                old_value = current.get("value__c")

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

    @staticmethod
    def _filter_eq(rows: Iterable[Dict[str, Any]], field: str, value: Any, *, case_sensitive: bool = False) -> List[
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
            if norm(v) == target:
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
        print(response)
        return self._status_err(response)

    def _update_attribute(self, update_obj) -> Tuple[Optional[int], Optional[str]]:
        data = [update_obj]
        request_object = {"data": data}
        response = self.ingestion_client.ingest_data(request_object, self.connector, self.dlo)
        print(response.json())
        return self._status_err(response)

    def _search_all_memories(self, user_id: str, **kwargs) -> Optional[httpx.Response]:
        """
        Fetches all current memories of a user
        """
        sql = f"""
            SELECT
                *
            FROM
                "AIUserAttributes__dlm"
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
