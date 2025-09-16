from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple, Union


@dataclass(frozen=True)
class Column:
    name: str
    order: int
    type: str  # e.g., 'VARCHAR', 'TIMESTAMP WITH TIME ZONE', 'DECIMAL'


def _parse_input(payload: Union[str, dict]) -> dict:
    """
    Accepts a JSON-ish string (single quotes, True/False/None) or a dict.
    Returns a Python dict.
    """
    if isinstance(payload, dict):
        return payload
    # Try standard JSON first
    try:
        return json.loads(payload)
    except Exception:
        # Fall back to safely parsing Python-literal-like strings
        return ast.literal_eval(payload)


def _columns_from_metadata(md: Dict[str, Dict[str, Any]]) -> List[Column]:
    cols: List[Column] = []
    for name, info in md.items():
        cols.append(Column(name=name,
                           order=int(info.get("placeInOrder", 0)),
                           type=str(info.get("type", "VARCHAR"))))
    # Sort by placeInOrder
    cols.sort(key=lambda c: c.order)
    return cols


def _coerce_value(value: Any, col_type: str) -> Any:
    if value is None:
        return None

    t = col_type.upper()
    if "TIMESTAMP" in t:
        # Accept forms like "2025-09-16 02:03:09.000 UTC" or ISO strings
        s = str(value)
        # Common " ... UTC" form → treat as UTC
        if s.endswith(" UTC"):
            s = s[:-4]
            for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
                try:
                    dt = datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
                    return dt.isoformat().replace("+00:00", "Z")
                except ValueError:
                    pass
        # Try ISO-8601-ish
        try:
            iso = s.replace("Z", "+00:00")
            dt = datetime.fromisoformat(iso)
            # normalize to Z
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt.isoformat().replace("+00:00", "Z")
        except Exception:
            return value  # leave as-is if all parsing fails

    if "DECIMAL" in t or "NUMERIC" in t or "DOUBLE" in t or "FLOAT" in t or "REAL" in t:
        try:
            return float(value)
        except Exception:
            return value

    # Default: return as-is (VARCHAR, etc.)
    return value


def parse_tabular_payload(
    payload: Union[str, dict],
    *,
    coerce_types: bool = True,
    passthrough_keys: Tuple[str, ...] = ("done", "startTime", "endTime", "rowCount", "queryId"),
) :
    """
    Transform the API output into a clean, well-formed structure.

    Returns:
    {
      "columns": ["value__c", "userId__c", ...],
      "rows": [
        {"value__c": "Delta Airlines", "userId__c": "makarand", ...},
        ...
      ],
      # plus selected passthrough keys if present
    }
    """
    obj = _parse_input(payload)

    data = obj.get("data") or []
    metadata = obj.get("metadata") or {}
    cols = _columns_from_metadata(metadata)

    # Build column list (ordered) and a parallel types list
    column_names = [c.name for c in cols]
    column_types = [c.type for c in cols]

    rows_out: List[Dict[str, Any]] = []
    for row in data:
        # Map each position to its column name; pad/truncate safely
        mapped: Dict[str, Any] = {}
        for idx, col_name in enumerate(column_names):
            raw = row[idx] if idx < len(row) else None
            if coerce_types:
                mapped[col_name] = _coerce_value(raw, column_types[idx])
            else:
                mapped[col_name] = raw
        rows_out.append(mapped)

    result = {
        "columns": column_names,
        "rows": rows_out,
    }

    for k in passthrough_keys:
        if k in obj:
            result[k] = obj[k]

    return result