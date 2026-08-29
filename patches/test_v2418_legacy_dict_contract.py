from legacy_dict_contract import (
    SCHEMA_ID, LegacyDictContractError, describe_legacy_dict_contract,
    validate_legacy_layout, validate_legacy_placement,
)

contract = describe_legacy_dict_contract()
assert contract["schema_id"] == SCHEMA_ID
assert contract["coordinate_unit"] == "mm"
assert contract["index_base"] == 0
assert contract["required_keys"] == ["x_mm", "y_mm", "page_index", "job_index"]

value = validate_legacy_placement({
    "x_mm": 12, "y_mm": 3.5, "page_index": 0, "job_index": 2, "rotation": 90
})
assert value["x_mm"] == 12.0
assert validate_legacy_layout([value]) == [value]

for bad in (
    {"x_mm": 1, "y_mm": 2, "page_index": 0},
    {"x_mm": "1", "y_mm": 2, "page_index": 0, "job_index": 0},
    {"x_mm": 1, "y_mm": 2, "page_index": -1, "job_index": 0},
    {"x_mm": 1, "y_mm": 2, "page_index": 0, "job_index": 0, "rotation": 45},
):
    try:
        validate_legacy_placement(bad)
    except LegacyDictContractError:
        pass
    else:
        raise AssertionError(bad)

print("V2.4.18 LEGACY DICT CONTRACT PASS")
