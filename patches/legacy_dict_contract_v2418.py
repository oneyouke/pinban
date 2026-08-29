from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

SCHEMA_ID = "desktop-imposer.layout-override.v1"
COORDINATE_UNIT = "mm"
INDEX_BASE = 0
REQUIRED_KEYS = ("x_mm", "y_mm", "page_index", "job_index")
OPTIONAL_KEYS = ("rotation", "width_mm", "height_mm")


class LegacyDictContractError(ValueError):
    pass


@dataclass(frozen=True)
class LegacyDictContract:
    schema_id: str = SCHEMA_ID
    coordinate_unit: str = COORDINATE_UNIT
    index_base: int = INDEX_BASE
    required_keys: tuple[str, ...] = REQUIRED_KEYS
    optional_keys: tuple[str, ...] = OPTIONAL_KEYS


def describe_legacy_dict_contract() -> dict[str, Any]:
    contract = LegacyDictContract()
    return {
        "schema_id": contract.schema_id,
        "coordinate_unit": contract.coordinate_unit,
        "index_base": contract.index_base,
        "required_keys": list(contract.required_keys),
        "optional_keys": list(contract.optional_keys),
    }


def validate_legacy_placement(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise LegacyDictContractError("legacy placement must be a mapping")
    missing = [key for key in REQUIRED_KEYS if key not in value]
    if missing:
        raise LegacyDictContractError("missing required keys: " + ", ".join(missing))
    result = dict(value)
    for key in ("x_mm", "y_mm"):
        if isinstance(result[key], bool) or not isinstance(result[key], (int, float)):
            raise LegacyDictContractError(f"{key} must be numeric millimetres")
        result[key] = float(result[key])
    for key in ("page_index", "job_index"):
        if isinstance(result[key], bool) or not isinstance(result[key], int) or result[key] < INDEX_BASE:
            raise LegacyDictContractError(f"{key} must be an integer >= {INDEX_BASE}")
    if "rotation" in result:
        if result["rotation"] not in (0, 90, 180, 270):
            raise LegacyDictContractError("rotation must be 0, 90, 180 or 270")
    return result


def validate_legacy_layout(values) -> list[dict[str, Any]]:
    if values is None:
        return []
    if isinstance(values, (str, bytes, Mapping)):
        raise LegacyDictContractError("legacy layout must be an iterable of placement mappings")
    return [validate_legacy_placement(value) for value in values]
