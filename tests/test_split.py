"""Stratified by-page split, exercised only through the CLI entry point on a fake metadata CSV."""
import csv
import random
from collections import Counter, defaultdict

import pytest

from eval.cli import main
from fakedata import CSV_FIELDS, write_page_csv


@pytest.fixture
def meta(tmp_path):
    path = tmp_path / "meta.csv"
    write_page_csv(path)
    return path


def run_split(csv_path, capsys):
    code = main(["split", "--csv", str(csv_path)])
    return code, capsys.readouterr().out


def read(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def side_of_pages(csv_path):
    sides = defaultdict(set)
    types = {}
    for r in read(csv_path):
        sides[r["page_id"]].add(r["split"])
        types[r["page_id"]] = r["doc_type"]
    return sides, types


def test_split_is_stratified_12_tuning_24_test(meta, capsys):
    code, out = run_split(meta, capsys)
    assert code == 0, out
    sides, types = side_of_pages(meta)
    counts = Counter((types[p], next(iter(s))) for p, s in sides.items())
    assert counts == {
        ("paper", "tuning"): 4, ("paper", "test"): 8,
        ("book", "tuning"): 3, ("book", "test"): 7,
        ("table", "tuning"): 3, ("table", "test"): 5,
        ("receipt", "tuning"): 2, ("receipt", "test"): 4,
    }


def test_every_image_of_a_page_is_on_the_same_side(meta, capsys):
    run_split(meta, capsys)
    sides, _ = side_of_pages(meta)
    assert len(sides) == 36
    assert all(len(s) == 1 and s <= {"tuning", "test"} for s in sides.values())


def test_same_seed_gives_same_split_regardless_of_row_order(tmp_path, capsys):
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    write_page_csv(a)
    write_page_csv(b)
    rows = read(b)
    random.Random(1).shuffle(rows)
    with open(b, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        w.writerows(rows)
    run_split(a, capsys)
    run_split(b, capsys)
    split_a = {r["filename"]: r["split"] for r in read(a)}
    split_b = {r["filename"]: r["split"] for r in read(b)}
    assert split_a == split_b


def test_other_columns_survive_the_write_back(meta, capsys):
    before = read(meta)
    run_split(meta, capsys)
    after = read(meta)
    assert [r["filename"] for r in after] == [r["filename"] for r in before]
    for b, a in zip(before, after):
        assert {k: v for k, v in a.items() if k != "split"} == {k: v for k, v in b.items() if k != "split"}


def test_phone_balance_is_reported_for_both_sides(meta, capsys):
    code, out = run_split(meta, capsys)
    sides, _ = side_of_pages(meta)
    phone = {r["page_id"]: r["phone_model"] for r in read(meta)}
    for side in ("tuning", "test"):
        pages = [p for p, s in sides.items() if s == {side}]
        n_a = sum(1 for p in pages if phone[p] == "A")
        line = next(l for l in out.splitlines() if l.startswith(f"phone balance {side}"))
        assert f"A {n_a} ({round(100 * n_a / len(pages))}%)" in line
        assert f"B {len(pages) - n_a} ({round(100 * (len(pages) - n_a) / len(pages))}%)" in line


def test_second_run_is_refused_and_changes_nothing(meta, capsys):
    run_split(meta, capsys)
    first = meta.read_bytes()
    code, out = run_split(meta, capsys)
    assert code == 1
    assert "already" in out and "split" in out
    assert meta.read_bytes() == first


def test_partly_split_csv_is_also_refused(meta, capsys):
    rows = read(meta)
    rows[0]["split"] = "test"
    with open(meta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        w.writerows(rows)
    before = meta.read_bytes()
    code, out = run_split(meta, capsys)
    assert code == 1
    assert meta.read_bytes() == before


def test_pilot_pages_always_land_in_tuning(tmp_path, capsys):
    # one pilot page per document type: p01 paper, p13 book, p23 table, p31 receipt
    for pilots in [(1, 13, 23, 31), (12, 22, 30, 36), (5, 15, 25, 33)]:
        path = tmp_path / f"meta{pilots[0]}.csv"
        write_page_csv(path, pilot_pages=pilots)
        code, out = run_split(path, capsys)
        assert code == 0, out
        sides, _ = side_of_pages(path)
        assert all(sides[f"p{p:02d}"] == {"tuning"} for p in pilots)
        assert sum(1 for s in sides.values() if s == {"tuning"}) == 12


def test_too_many_pilot_pages_for_a_type_is_an_error_naming_the_type(tmp_path, capsys):
    path = tmp_path / "meta.csv"
    write_page_csv(path, pilot_pages=(31, 32, 33))  # three receipts, only 2 tuning slots
    before = path.read_bytes()
    code, out = run_split(path, capsys)
    assert code == 1
    assert "receipt" in out and "pilot" in out
    assert path.read_bytes() == before


def test_doc_type_with_a_single_page_cannot_appear_on_both_sides(tmp_path, capsys):
    path = tmp_path / "meta.csv"
    write_page_csv(path, {"paper": 12, "book": 10, "table": 8, "receipt": 1})
    before = path.read_bytes()
    code, out = run_split(path, capsys)
    assert code == 1
    assert "receipt" in out
    assert path.read_bytes() == before


def test_small_dataset_still_has_every_type_on_both_sides(tmp_path, capsys):
    path = tmp_path / "meta.csv"
    write_page_csv(path, {"paper": 3, "book": 3, "table": 2, "receipt": 2})
    code, out = run_split(path, capsys)
    assert code == 0, out
    sides, types = side_of_pages(path)
    for t in ("paper", "book", "table", "receipt"):
        assert {next(iter(s)) for p, s in sides.items() if types[p] == t} == {"tuning", "test"}


def test_unknown_doc_type_names_the_row(tmp_path, capsys):
    path = tmp_path / "meta.csv"
    write_page_csv(path, {"paper": 12, "book": 10, "table": 8, "receipt": 5, "poster": 1})
    code, out = run_split(path, capsys)
    assert code == 1
    assert "poster" in out and "p36" in out
