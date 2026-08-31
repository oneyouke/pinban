import json
import tempfile
from pathlib import Path

from pypdf import PdfReader
from reportlab.pdfgen import canvas

from card_deck import MM_TO_PT, export_card_deck_pdf, load_card_manifest, plan_card_deck, validate_deck


def sample(path, labels):
    c = canvas.Canvas(str(path), pagesize=(63 * MM_TO_PT, 88 * MM_TO_PT))
    for label in labels:
        c.setFont("Helvetica", 16); c.drawString(20, 100, label); c.showPage()
    c.save()


with tempfile.TemporaryDirectory(prefix="v2426-card-deck-") as td:
    root = Path(td); ids = ["A", "B", "C", "D", "E"]
    fronts = root / "fronts.pdf"; common_back = root / "common-back.pdf"; paired_backs = root / "paired-backs.pdf"
    sample(fronts, [f"FRONT-{x}" for x in ids]); sample(common_back, ["COMMON-BACK"]); sample(paired_backs, [f"BACK-{x}" for x in ids])
    manifest = root / "deck.json"; manifest.write_text(json.dumps({"cards": ids, "expected_ids": ids}), encoding="utf-8")
    loaded, expected = load_card_manifest(manifest); assert loaded == ids and expected == ids
    assert validate_deck(loaded, expected).okay
    invalid = validate_deck(["A", "B", "B", "E"], ["A", "B", "C", "D"])
    assert not invalid.okay and invalid.duplicates == ["B"] and invalid.missing == ["C", "D"] and invalid.unexpected == ["E"]

    common_output = root / "common-output.pdf"
    common = export_card_deck_pdf(
        fronts, common_back, common_output, sheet_width_mm=210, sheet_height_mm=120,
        trim_width_mm=63, trim_height_mm=88, rows=1, columns=3,
        gap_x_mm=5, common_back=True, flip="long_edge", manifest_path=manifest,
    )
    reader = PdfReader(str(common_output)); assert common["sheet_count"] == 2 and common["output_pages"] == 4 and common["blank_cards"] == 1
    assert all(f"FRONT-{x}" in (reader.pages[0].extract_text() or "") for x in ids[:3])
    assert (reader.pages[1].extract_text() or "").count("COMMON-BACK") == 3
    all_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    for x in ids: assert all_text.count(f"FRONT-{x}\n") == 1
    assert all_text.count("COMMON-BACK") == 5

    paired_output = root / "paired-output.pdf"
    paired = export_card_deck_pdf(
        fronts, paired_backs, paired_output, sheet_width_mm=210, sheet_height_mm=120,
        trim_width_mm=63, trim_height_mm=88, rows=1, columns=3,
        gap_x_mm=5, common_back=False, flip="short_edge", manifest_path=manifest,
    )
    paired_reader = PdfReader(str(paired_output)); assert paired["common_back"] is False
    assert all(f"BACK-{x}" in (paired_reader.pages[1].extract_text() or "") for x in ids[:3])
    assert paired["pairs"][2] == {"card_id": "C", "front_page": 3, "back_page": 3}
    plan = plan_card_deck(ids, sheet_width_mm=210, sheet_height_mm=120, trim_width_mm=63, trim_height_mm=88, rows=1, columns=3, gap_x_mm=5, flip="self_turn")
    assert all(p.rotation == 180 for p in plan.placements if p.side == "back")

    csv_manifest = root / "deck.csv"; csv_manifest.write_text("card_id\nA\nB\nC\nD\nE\n", encoding="utf-8")
    csv_ids, csv_expected = load_card_manifest(csv_manifest); assert csv_ids == ids and csv_expected is None
print("V2.4.26 CARD DECK PAIRING PASS")
