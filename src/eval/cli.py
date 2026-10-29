"""Dataset tool:
  python -m eval.cli validate --csv meta.csv --images IMG_DIR --pdfs PDF_DIR
  python -m eval.cli split --csv meta.csv
  python -m eval.cli report --csv meta.csv --images IMG_DIR --pdfs PDF_DIR --out OUT_DIR
  python -m eval.cli public --root PUBLIC_DIR --out OUT_DIR
  python -m eval.cli template --pages pages.csv --csv meta.csv --checklist shotlist.md"""
import argparse
import json
import sys
from pathlib import Path

from collections import Counter

from .baseline import ReportError, run_baseline
from .plot import plot_page_cer
from .public import run_public, write_results
from .template import TemplateError, build_template, write_template
from .report import MIN_PAGES_FOR_VERDICT, build_summary, describe_shortfall, flagged_gap_lines, render_markdown
from .dataset import DOC_TYPES, MIN_GT_CHARS, SPLIT_SEED, SPLITS, SplitError, split_dataset, validate_dataset


def _validate(args: argparse.Namespace) -> int:
    rep = validate_dataset(args.csv, args.images, args.pdfs, args.min_chars)
    for msg in rep.errors:
        print(f"ERROR: {msg}")
    for msg in rep.warnings:
        print(f"WARNING: {msg}")
    summary = (
        f"{rep.n_images} images, {rep.n_pages} pages, {len(rep.errors)} error(s), {len(rep.warnings)} warning(s)"
    )
    print(f"{'FAILED' if rep.errors else 'OK'}: {summary}")
    return 1 if rep.errors else 0


def _split(args: argparse.Namespace) -> int:
    try:
        res = split_dataset(args.csv)
    except SplitError as e:
        print(f"ERROR: {e}")
        return 1
    for side in SPLITS:
        pages = [p for p, s in res.side_of.items() if s == side]
        per_type = Counter(res.types[p] for p in pages)
        print(f"{side}: {len(pages)} pages ("
              + ", ".join(f"{t} {per_type[t]}" for t in DOC_TYPES if t in per_type) + ")")
    for side in SPLITS:
        phones = Counter(res.phones[p] or "unknown" for p, s in res.side_of.items() if s == side)
        total = sum(phones.values())
        print(f"phone balance {side}: "
              + ", ".join(f"{ph} {n} ({round(100 * n / total)}%)" for ph, n in sorted(phones.items())))
    print(f"OK: split written to {args.csv} (seed {SPLIT_SEED}); it is final and will not be overwritten")
    return 0


def _verdict_stdout(title: str, verdict: dict) -> None:
    ok = all(v["passed"] for v in verdict.values())
    print(f"{title}: {'PASS' if ok else 'FAIL'}")
    for cond, v in verdict.items():
        if v["status"] == "no data":
            print(f"  {cond}: no data")
        elif v["passed"]:
            print(f"  {cond}: pass (+{100 * v['gap']:.1f} pts over clean, "
                  f"{v['n_above']}/{v['n_images']} images above their page's clean)")
        else:
            print(f"  {cond}: FAIL (+{100 * v['gap']:.1f} pts over clean) - {describe_shortfall(v)}")


def _report(args: argparse.Namespace) -> int:
    try:
        base = run_baseline(args.csv, args.images, args.pdfs, args.out, args.precomputed)
    except ReportError as e:
        print(f"ERROR: {e}")
        return 1
    summary = build_summary(base.records)
    args.out.mkdir(parents=True, exist_ok=True)
    plot_page_cer(summary, args.out / "cer_by_page.png")
    (args.out / "baseline_summary.json").write_text(
        json.dumps({"header": base.header, **summary}, ensure_ascii=False, indent=1), encoding="utf-8")
    (args.out / "baseline_report.md").write_text(
        render_markdown(summary, base.header, "cer_by_page.png"), encoding="utf-8")
    print(f"OCR run on {base.n_ocr} image(s), {base.n_cached} reused from the stored results")
    for t in summary["flagged_types"]:
        print(f"FLAG: {t} clean-baseline CER {100 * summary['clean_cer_by_type'][t]:.1f}% > 20%, "
              "discuss separately")
    if summary["pilot"] is None:
        print("Pilot verdict: no pilot images flagged in the CSV")
    else:
        _verdict_stdout("Pilot verdict", summary["pilot"])
    scope = "excluding flagged types" if summary["flagged_types"] else "all pages"
    _verdict_stdout(f"Stage exit (blur/shadow/persp clearly above clean, {scope})", summary["stage_exit"])
    if summary["few_page_conditions"]:
        print(f"NOTE: few pages judged (< {MIN_PAGES_FOR_VERDICT}) for {', '.join(summary['few_page_conditions'])}; "
              "treat the verdict as indicative only")
    if summary["flagged_types"]:
        print(f"excluded from the verdicts: {', '.join(summary['flagged_types'])} (clean CER > 20%); gaps over their own clean:")
        for line in flagged_gap_lines(summary):
            print(f"  {line[2:]}")
    print(f"OK: report written to {args.out}")
    return 0


def _public(args: argparse.Namespace) -> int:
    try:
        results, n_ocr, n_cached = run_public(args.root, args.out, args.ocr_texts)
    except ReportError as e:
        print(f"ERROR: {e}")
        return 1
    write_results(results, args.out)
    print(f"OCR run on {n_ocr} image(s), {n_cached} reused from the stored results")
    for res in results:
        print(f"{res.dataset}: {len(res.records)} image(s), reference: {res.reference} "
              f"-> {args.out / f'public_{res.dataset}.md'}")
    print(f"OK: {len(results)} table(s) written to {args.out}, one per reference source")
    return 0


def _template(args: argparse.Namespace) -> int:
    for out in (args.csv, args.checklist):
        if out.exists():
            print(f"ERROR: {out} already exists; it is never overwritten (shooting notes may live in it)")
            return 1
    try:
        tpl = build_template(args.pages)
    except TemplateError as e:
        print(f"ERROR: {e}")
        return 1
    for msg in tpl.warnings:
        print(msg)
    write_template(tpl, args.csv, args.checklist)
    print(f"OK: {len(tpl.rows)} rows for {len({r['page_id'] for r in tpl.rows})} pages -> {args.csv}; "
          f"shot list -> {args.checklist}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="mode", required=True)
    v = sub.add_parser("validate", help="check the dataset against the capture protocol")
    v.add_argument("--csv", type=Path, required=True, help="metadata CSV")
    v.add_argument("--images", type=Path, required=True, help="directory of captured JPEGs")
    v.add_argument("--pdfs", type=Path, required=True, help="directory of source PDFs")
    v.add_argument("--min-chars", type=int, default=MIN_GT_CHARS,
                   help=f"warn when a page's normalized text is shorter (default {MIN_GT_CHARS})")
    v.set_defaults(run=_validate)
    sp = sub.add_parser("split", help="stratified by-page tuning/test split, written into the CSV")
    sp.add_argument("--csv", type=Path, required=True, help="metadata CSV (its split column is filled in)")
    sp.set_defaults(run=_split)
    r = sub.add_parser("report", help="P0 baseline: OCR every image, condition x doc-type tables, pilot verdict")
    r.add_argument("--csv", type=Path, required=True, help="metadata CSV")
    r.add_argument("--images", type=Path, required=True, help="directory of captured JPEGs")
    r.add_argument("--pdfs", type=Path, required=True, help="directory of source PDFs")
    r.add_argument("--out", type=Path, required=True, help="output directory (results, report, plot)")
    r.add_argument("--precomputed", type=Path,
                   help="JSON of filename -> {cer, wer}: use these numbers instead of running OCR")
    r.set_defaults(run=_report)
    pb = sub.add_parser("public", help="public-dataset tables, one per reference source (ADR-0002)")
    pb.add_argument("--root", type=Path, required=True, help="directory holding smartdoc_qa/ and/or rdd/")
    pb.add_argument("--out", type=Path, required=True, help="output directory (one report per dataset)")
    pb.add_argument("--ocr-texts", type=Path,
                    help="JSON of '<dataset>/<filename>' -> raw OCR text: use these instead of running OCR")
    pb.set_defaults(run=_public)
    t = sub.add_parser("template", help="metadata CSV skeleton and shot list from a page list")
    t.add_argument("--pages", type=Path, required=True,
                   help="page list CSV: page_id, doc_type, pdf_file, pdf_page [, phone_model, pilot]")
    t.add_argument("--csv", type=Path, required=True, help="metadata CSV skeleton to write (must not exist)")
    t.add_argument("--checklist", type=Path, required=True, help="shot list markdown to write (must not exist)")
    t.set_defaults(run=_template)
    args = ap.parse_args(argv)
    try:
        return args.run(args)
    except (OSError, UnicodeDecodeError) as e:
        print(f"ERROR: cannot read dataset: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
