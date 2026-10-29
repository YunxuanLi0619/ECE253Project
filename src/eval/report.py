"""Aggregation of per-image P0 results into the baseline report (ADR-0001 conventions).

Cells are macro averages: images of one page+condition are averaged first, then pages. Micro averages
(total errors / total characters) are kept for an appendix table."""
import random
from collections import defaultdict
from statistics import mean, median

from .dataset import CONDITIONS, DOC_TYPES

BOOTSTRAP_SEED = 253
BOOTSTRAP_RESAMPLES = 2000
MIN_PAGES_FOR_CI = 5
POOR_BASELINE_CER = 0.20  # clean-baseline CER above this flags a document type (and a page)
PILOT_GAP = 0.05  # condition mean must beat the clean baseline by this much (absolute CER)
PILOT_FRACTION = (2, 3)  # at least this share of images must be above their page's baseline
POOR_BASELINE_RATIO = 1.5  # ... or at least this multiple when the page's own baseline is poor
JUDGED = ("blur", "shadow", "persp")
MIN_PAGES_FOR_VERDICT = 3  # a verdict resting on fewer judged pages is flagged as indicative only
METRICS = ("cer", "wer")
OVERALL = "overall"  # pooled over pages of the types not flagged as poor-baseline
EPS = 1e-9


def _page_means(records: list[dict], metric: str) -> dict[tuple[str, str], tuple[str, float]]:
    """(condition, page) -> (doc_type, mean metric over that page+condition's images)."""
    groups: dict[tuple[str, str], list[float]] = defaultdict(list)
    types: dict[str, str] = {}
    for r in records:
        groups[(r["condition"], r["page_id"])].append(r[metric])
        types[r["page_id"]] = r["doc_type"]
    return {key: (types[key[1]], mean(vals)) for key, vals in groups.items()}


def _bootstrap_ci(values: list[float]) -> list[float]:
    rng = random.Random(BOOTSTRAP_SEED)
    n = len(values)
    means = sorted(mean(rng.choices(values, k=n)) for _ in range(BOOTSTRAP_RESAMPLES))
    return [means[int(0.025 * BOOTSTRAP_RESAMPLES)], means[int(0.975 * BOOTSTRAP_RESAMPLES) - 1]]


def _cell(values: list[float]) -> dict | None:
    if not values:
        return None
    return {"n": len(values), "mean": mean(values), "median": median(values),
            "ci": _bootstrap_ci(values) if len(values) >= MIN_PAGES_FOR_CI else None}


def _micro(records: list[dict], metric: str) -> dict | None:
    n_key = "char_N" if metric == "cer" else "word_N"
    total = sum(r[n_key] for r in records)
    if not total:
        return None
    return {"n_images": len(records), "value": sum(r[metric] * r[n_key] for r in records) / total}


def judge(records: list[dict]) -> dict:
    """Is each defect clearly worse than the clean baseline? (pilot rule, ADR / stage-1 decisions)

    Pass needs both: the condition's page-level mean CER at least PILOT_GAP above the clean mean,
    and at least 2/3 of its images above their own page's clean CER (>= 1.5x when that page's clean
    CER is itself above POOR_BASELINE_CER). Pages without a clean image cannot be judged."""
    clean: dict[str, list[float]] = defaultdict(list)
    for r in records:
        if r["condition"] == "clean":
            clean[r["page_id"]].append(r["cer"])
    base = {p: mean(v) for p, v in clean.items()}
    out = {}
    for cond in JUDGED:
        imgs = [r for r in records if r["condition"] == cond and r["page_id"] in base]
        if not imgs:
            out[cond] = {"status": "no data", "passed": False}
            continue
        pages = sorted({r["page_id"] for r in imgs})
        cond_mean = mean(mean(r["cer"] for r in imgs if r["page_id"] == p) for p in pages)
        clean_mean = mean(base[p] for p in pages)
        gap = cond_mean - clean_mean
        above = sum(
            r["cer"] >= POOR_BASELINE_RATIO * base[r["page_id"]] - EPS
            if base[r["page_id"]] > POOR_BASELINE_CER else r["cer"] > base[r["page_id"]] + EPS
            for r in imgs)
        num, den = PILOT_FRACTION
        gap_ok = gap >= PILOT_GAP - EPS
        frac_ok = above * den >= num * len(imgs)
        out[cond] = {
            "status": "pass" if gap_ok and frac_ok else "fail", "passed": gap_ok and frac_ok,
            "n_images": len(imgs), "n_pages": len(pages),
            "cond_mean": cond_mean, "clean_mean": clean_mean, "gap": gap,
            "gap_shortfall": max(0.0, PILOT_GAP - gap),
            "n_above": above, "frac_above": above / len(imgs),
        }
    return out


def build_summary(records: list[dict]) -> dict:
    types = [t for t in DOC_TYPES if any(r["doc_type"] == t for r in records)]
    conds = [c for c in CONDITIONS if any(r["condition"] == c for r in records)]

    cer_pages = _page_means(records, "cer")
    clean_by_type = {
        t: mean(v for (c, _), (tt, v) in cer_pages.items() if c == "clean" and tt == t)
        for t in types if any(c == "clean" and tt == t for (c, _), (tt, _) in cer_pages.items())}
    flagged = [t for t in types if clean_by_type.get(t, 0.0) > POOR_BASELINE_CER]

    cells, micro = {}, {}
    for metric in METRICS:
        pages = _page_means(records, metric)
        cells[metric], micro[metric] = {}, {}
        for cond in conds:
            row, mrow = {}, {}
            for t in types:
                row[t] = _cell([v for (c, _), (tt, v) in pages.items() if c == cond and tt == t])
                mrow[t] = _micro([r for r in records if r["condition"] == cond and r["doc_type"] == t], metric)
            keep = [t for t in types if t not in flagged]
            row[OVERALL] = _cell([v for (c, _), (tt, v) in pages.items() if c == cond and tt in keep])
            mrow[OVERALL] = _micro(
                [r for r in records if r["condition"] == cond and r["doc_type"] in keep], metric)
            cells[metric][cond], micro[metric][cond] = row, mrow

    pilot_rows = [r for r in records if r["pilot"] and r["condition"] != "clean"]
    pilot_pages = {r["page_id"] for r in pilot_rows}
    pilot = None
    if pilot_rows:
        scope = [r for r in records if r["page_id"] in pilot_pages and (r["pilot"] or r["condition"] == "clean")]
        pilot = judge(scope)
    # The stage-exit verdict leaves out flagged (poor-baseline) types, like the pooled column; those
    # types get their gaps listed separately for discussion and never decide whether a defect is clearly
    # worse. The pilot verdict keeps them: its 1.5x rule is made for pages whose own baseline is poor.
    stage_exit = judge([r for r in records if r["doc_type"] not in flagged])
    return {
        "doc_types": types, "conditions": conds, "flagged_types": flagged,
        "clean_cer_by_type": clean_by_type, "cells": cells, "micro": micro,
        "pilot": pilot, "stage_exit": stage_exit,
        "flagged_verdicts": {t: judge([r for r in records if r["doc_type"] == t]) for t in flagged},
        "few_page_conditions": few_page_conditions(stage_exit),
        "page_cer": {f"{c}|{p}": v for (c, p), (_, v) in cer_pages.items()},
        "page_types": {r["page_id"]: r["doc_type"] for r in records},
    }


def _pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def _fmt_cell(c: dict | None) -> str:
    if c is None:
        return "–"
    ci = f" [{_pct(c['ci'][0])}, {_pct(c['ci'][1])}]" if c["ci"] else " n too small"
    return f"{_pct(c['mean'])}{ci} (n={c['n']}, median {_pct(c['median'])})"


def _table(rows: dict, conds: list[str], cols: list[str], headers: dict[str, str], fmt) -> list[str]:
    lines = ["| Condition | " + " | ".join(headers[c] for c in cols) + " |", "|" + "---|" * (len(cols) + 1)]
    for cond in conds:
        lines.append(f"| {cond} | " + " | ".join(fmt(rows[cond][c]) for c in cols) + " |")
    return lines


def _verdict_lines(verdict: dict) -> list[str]:
    lines = []
    for cond, v in verdict.items():
        if v["status"] == "no data":
            lines.append(f"- **{cond}**: no data (missing images or clean baseline)")
            continue
        lines.append(
            f"- **{cond}**: {'pass' if v['passed'] else 'fail'} — mean CER {_pct(v['cond_mean'])}, "
            f"clean baseline {_pct(v['clean_mean'])}, {100 * v['gap']:.1f} points higher"
            f" (need ≥ {100 * PILOT_GAP:.1f}); {v['n_above']}/{v['n_images']} images above the page baseline"
            f" (need ≥ {PILOT_FRACTION[0]}/{PILOT_FRACTION[1]})")
        if not v["passed"]:
            lines.append("  - Shortfall: " + describe_shortfall(v))
    return lines


def few_page_conditions(verdict: dict) -> list[str]:
    """Conditions whose verdict rests on fewer than MIN_PAGES_FOR_VERDICT judged pages."""
    return [c for c, v in verdict.items() if v["status"] != "no data" and v["n_pages"] < MIN_PAGES_FOR_VERDICT]


def flagged_gap_lines(summary: dict) -> list[str]:
    """One line per flagged type: its CER gap over its own clean baseline, per defect."""
    lines = []
    for t, verdict in summary["flagged_verdicts"].items():
        gaps = ", ".join(f"{c} {100 * v['gap']:+.1f} points" for c, v in verdict.items() if v["status"] != "no data")
        lines.append(f"- {t} (clean baseline {_pct(summary['clean_cer_by_type'][t])}): {gaps or 'no data'}")
    return lines


def describe_shortfall(v: dict) -> str:
    """What a failing condition lacks, in plain words."""
    parts = []
    if v["gap"] < PILOT_GAP - EPS:
        parts.append(f"mean gap short by {100 * v['gap_shortfall']:.1f} points")
    num, den = PILOT_FRACTION
    if v["n_above"] * den < num * v["n_images"]:
        parts.append(f"only {v['n_above']}/{v['n_images']} images above the baseline, need ≥ {num}/{den}")
    return "; ".join(parts)


def render_markdown(summary: dict, header: dict, plot_name: str) -> str:
    types, conds, flagged = summary["doc_types"], summary["conditions"], summary["flagged_types"]
    cols = types + [OVERALL]
    headers = {t: f"{t} ⚠" if t in flagged else t for t in types}
    headers[OVERALL] = "Overall (excl. ⚠ types)" if flagged else "Overall"
    out = ["# P0 Baseline Report", "", "## Evaluation Configuration", ""]
    out += [f"- {k}: {json_value}" for k, json_value in header.items()]
    out += ["", "## Main Table: Condition × Document Type (CER)", "",
            "Cells are page-level macro-averages (first average the images of the same page and condition, then average over pages); n = number of pages; "
            f"a by-page bootstrap 95% interval is given only for n ≥ {MIN_PAGES_FOR_CI}.", ""]
    out += _table(summary["cells"]["cer"], conds, cols, headers, _fmt_cell)
    if flagged:
        out += ["", "⚠ Types with clean-baseline CER above 20% (discussed separately, not folded into Overall): "
                + ", ".join(f"{t}({_pct(summary['clean_cer_by_type'][t])})" for t in flagged)]
    out += ["", "## Main Table: Condition × Document Type (WER)", ""]
    out += _table(summary["cells"]["wer"], conds, cols, headers, _fmt_cell)
    out += ["", "## Per-Page CER Distribution", "", f"![Per-page CER distribution]({plot_name})", ""]
    if summary["pilot"] is not None:
        passed = all(v["passed"] for v in summary["pilot"].values())
        out += ["## Pilot Verdict", "", f"**{'All conditions pass' if passed else 'Some conditions fail, reshoot needed'}**", ""]
        out += _verdict_lines(summary["pilot"]) + [""]
    exit_ok = all(v["passed"] for v in summary["stage_exit"].values())
    scope = "over pages not excluded as ⚠" if flagged else "over all pages"
    out += ["## Stage Exit Status", "",
            f"Are blur, shadow and perspective all clearly above the clean baseline (same rule as the pilot verdict, {scope}): **{'yes' if exit_ok else 'no'}**", ""]
    out += _verdict_lines(summary["stage_exit"]) + [""]
    if summary["few_page_conditions"]:
        out += [f"Too few pages: {', '.join(summary['few_page_conditions'])} judged on fewer than {MIN_PAGES_FOR_VERDICT} pages, "
                "verdict for reference only.", ""]
    if flagged:
        out += [f"Excluded ⚠ types: {', '.join(flagged)} (clean-baseline CER above {100 * POOR_BASELINE_CER:.0f}%). "
                "Below is each defect's CER gap to its clean baseline, for separate discussion only and not counted in the pass/fail verdict:", ""]
        out += flagged_gap_lines(summary) + [""]
    out += ["## Appendix: Micro-Average (total errors / total characters or words)", ""]
    for metric in METRICS:
        out += [f"### {metric.upper()}", ""]
        out += _table(summary["micro"][metric], conds, cols, headers,
                      lambda m: "–" if m is None else f"{_pct(m['value'])} ({m['n_images']} images)")
        out += [""]
    return "\n".join(out)
