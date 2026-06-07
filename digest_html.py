#!/usr/bin/env python3
"""digest_html.py — the clinician-facing Pre-visit Pattern Digest (UI slice 2).

Pure stdlib. Zero external dependencies. Local-only: the output is a SINGLE
self-contained .html file (inline CSS/JS, no CDN, no external src, no network), so
it opens offline and can be handed to a reviewer as-is.

This is the PRODUCT view the Figma mock specified
(https://www.figma.com/design/BcT7yhsMHAZl2AeJD9fAAK) — distinct from
report_html.py, which stays the working/inspection view. ADR 0014 drew that
two-views split; ADR 0015 records this digest.

It renders the five surfacing lenses as neutral cards beside the cited source
note: each card states what was surfaced and carries a ``cited:`` chip of its
provenance dates; clicking a card highlights its cited spans in the note. The
cards come from run_report() over real extracted records — never hand-written —
so the view can only ever show what the engine actually surfaced.

Like the engine, it honors the librarian rule in the VIEW layer: a calm, low-stimulation
theme with a single NON-semantic accent (the same for every lens — no per-lens or severity
colors), light-first with an optional dark toggle, document order, surfaces/counts/
cites. It does NOT score, rank, judge, order by importance, or say what a pattern means.

The shared theme + neutral-span helpers + multi-patient chrome live in view_html.py
(the dependency floor, ADR 0021); this module keeps only the digest's card idiom.

  Demo:        python digest_html.py --demo [outfile.html]
  Multi-batch: python digest_html.py --demo-multi [outfile.html]
"""

from __future__ import annotations

import argparse
import datetime
import sys

from extract import MultiExtractResult, extract_records, extract_records_multi
from recurrence import RecordReport, run_report

# Shared, pure view primitives — one source of truth for span collection, neutral
# <mark> rendering, HTML-escaping, the click-to-highlight scripts, and the
# multi-patient chrome (jump-index, quarantine, per-patient scoped JS), so the
# inspection view and this digest can never highlight provenance differently.
from view_html import (
    _JS,
    _MULTI_CHROME_CSS,
    _MULTI_JS,
    _PRINT_CSS,
    _THEME_CSS,
    _THEME_JS,
    _THEME_MEDIA_CSS,
    _anchor_id,
    _collect_spans,
    _esc,
    _localized_note,
    _render_note,
    _render_patient_index,
    _render_quarantine,
)

VERSION = "0.3.0"

# Lens label shown on each card: the engine's own neutral provenance name,
# presented for the clinician. Never a ranking or a judgment.
_LENS_LABELS = {
    "recurrence": "RECURRENCE",
    "gap": "GAP / RETURN",
    "frequency": "FREQUENCY",
    "cooccurrence": "CO-OCCURRENCE",
    "cadence_change": "CADENCE CHANGE",
}


def _card_parts(finding: object) -> tuple[str, str, str, list[str], list[str] | None]:
    """Return ``(lens_label, neutral_line, cited_chip, item_labels, cited_dates)``
    for one finding, built straight from its typed hit.

    The line states only what was surfaced; the chip cites the provenance dates.
    No severity, no direction (faster/slower), no ranking, no interpretation.
    ``item_labels`` link the card to its highlighted source spans (co-occurrence
    carries two). ``cited_dates`` is the bare list of provenance dates for the
    list-of-dates lenses (recurrence, co-occurrence) so the view can collapse a
    long list to a count; it is ``None`` for lenses whose chip is already short
    (gap brackets, a frequency window, a cadence pivot)."""
    hit = finding.hit  # type: ignore[attr-defined]
    lens = finding.expert  # type: ignore[attr-defined]
    label = _LENS_LABELS.get(lens, lens.upper())
    dates: list[str] | None = None
    if lens == "recurrence":
        line = f"{hit.item} — surfaced on {hit.count} dates"
        dates = list(hit.dates)
        chip = "cited: " + ", ".join(dates)
        items = [hit.item]
    elif lens == "gap":
        line = f"{hit.item} — {hit.gap_days}-day gap before it surfaced again"
        chip = f"cited: {hit.before_date} → {hit.after_date}"
        items = [hit.item]
    elif lens == "frequency":
        span_days = (
            datetime.date.fromisoformat(hit.window_end)
            - datetime.date.fromisoformat(hit.window_start)
        ).days
        line = f"{hit.item} — {hit.count} mentions within {span_days} days"
        chip = f"cited: {hit.window_start} … {hit.window_end}"
        items = [hit.item]
    elif lens == "cooccurrence":
        line = f"{hit.item_a} + {hit.item_b} — appeared together on {hit.count} dates"
        dates = list(hit.dates)
        chip = "cited: " + ", ".join(dates)
        items = [hit.item_a, hit.item_b]
    elif lens == "cadence_change":
        line = (
            f"{hit.item} — spacing changed, about {hit.before_interval} days "
            f"to about {hit.after_interval} days"
        )
        chip = f"cited: pivot {hit.pivot_date}"
        items = [hit.item]
    else:  # pragma: no cover - a future lens renders its own neutral line
        line = getattr(finding, "line", "")
        chip = ""
        items = []
    return label, line, chip, items, dates


# A list of cited dates longer than this is collapsed to a "cited: N dates"
# summary (tap/click to expand) so the clinician card stays scannable; the full
# dates are still in the document, one click away. Short lists render inline.
_CITES_COLLAPSE_OVER = 3


def _chip_html(chip: str, dates: list[str] | None) -> str:
    """The cited-provenance pill. A long list of dates (recurrence / co-occurrence)
    collapses to a ``cited: N dates`` summary that expands on tap; everything else
    — and any short list — renders as a plain inline pill. Counting and citing
    only; no judgment."""
    if dates is not None and len(dates) > _CITES_COLLAPSE_OVER:
        full = _esc(", ".join(dates))
        return (
            '<details class="chip cites">'
            f"<summary>cited: {len(dates)} dates</summary>"
            f'<div class="cites-full">{full}</div>'
            "</details>"
        )
    return f'<div class="chip">{_esc(chip)}</div>' if chip else ""


def _render_cards(reports: list[RecordReport]) -> str:
    """The surfaced lenses as cards, in the engine's registry order (recurrence,
    gap, frequency, co-occurrence, cadence change) — provenance order, not
    importance. Each card keeps ``data-items`` so a click lights up its cited
    source spans. An empty report surfaces nothing; it never asserts 'clean'."""
    cards: list[str] = []
    for report in reports:
        for finding in report.findings:
            label, line, chip, items, dates = _card_parts(finding)
            data_items = _esc("|".join(items))
            chip_html = _chip_html(chip, dates)
            cards.append(
                f'<div class="card finding" data-items="{data_items}"'
                ' tabindex="0" role="button" aria-pressed="false">'
                f'<div class="lens">{_esc(label)}</div>'
                f'<div class="line">{_esc(line)}</div>'
                f"{chip_html}"
                f"</div>"
            )
    if not cards:
        return '<p class="empty">No patterns surfaced. (The record is not asserted clean.)</p>'
    return "\n".join(cards)


# Layout only — colour/typography/components live in _THEME_CSS (shared).
_CSS = """\
main { display: flex; gap: 0; align-items: stretch; }
section { padding: 20px 28px; }
.patterns { flex: 1 1 58%; border-inline-end: 1px solid var(--border); }
.source { flex: 1 1 42%; }
.card { border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px;
        margin: 0 0 12px; background: var(--surface); }
.card:hover { border-color: var(--accent-line); }
.card.sel { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-weak); }
.lens { font-size: 10px; letter-spacing: .08em; }
.line { font-size: 15px; color: var(--text); margin: 5px 0 0; }
.chip { display: inline-block; margin: 10px 0 0; padding: 2px 9px; font-size: 11px;
        color: var(--muted); background: var(--mark-rest); border: 1px solid var(--border);
        border-radius: 999px; }
.chip.cites { padding: 0; border: none; background: none; }
.chip.cites > summary { display: inline-block; cursor: pointer; list-style: none;
        padding: 4px 11px; min-block-size: 28px; color: var(--muted); background: var(--mark-rest);
        border: 1px solid var(--border); border-radius: 999px; }
.chip.cites > summary::-webkit-details-marker { display: none; }
.chip.cites > summary:hover, .chip.cites[open] > summary { border-color: var(--accent-line); }
.cites-full { margin: 8px 0 0; font-size: 11px; color: var(--muted); line-height: 1.7; }
"""


def render_digest(
    note: str,
    records: list[dict],
    reports: list[RecordReport],
    *,
    title: str = "Pre-visit Pattern Digest",
    reference_date: datetime.date | None = None,
) -> str:
    """A single self-contained HTML document: the five surfaced lenses as neutral
    cards beside the cited source note, linked by a click. Pure string templating
    — no external resources, no network. Surfaces and cites; it does not judge,
    order, or recommend."""
    note_html = _render_note(note, _collect_spans(records))
    cards_html = _render_cards(reports)
    patient = next((r["id"] for r in records if r.get("id")), "")
    meta_bits = []
    if patient:
        meta_bits.append(f"Patient {patient}")
    if reference_date is not None:
        meta_bits.append(f"Encounter {reference_date.isoformat()}")
    meta_bits.append("de-identified")
    meta = " &middot; ".join(_esc(b) for b in meta_bits)
    return f"""<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(title)}</title>
<style>
{_THEME_CSS}{_CSS}{_THEME_MEDIA_CSS}{_PRINT_CSS}</style>
<script>
{_THEME_JS}</script>
</head>
<body>
<header>
<button class="theme-toggle" type="button">Dark</button>
<h1>{_esc(title)}</h1>
<p class="meta">{meta}</p>
<p class="stance">Surfaced from the record and cited &mdash; never judged, ordered, or recommended.
The clinician decides.</p>
</header>
<main>
<section class="patterns">
<h2>Surfaced patterns (click a line to highlight its source)</h2>
{cards_html}
</section>
<section class="source">
<h2>Source (cited)</h2>
<div class="note">{note_html}</div>
</section>
</main>
<footer>Health Prototype &middot; librarian layer &middot; synthetic data &middot;
generated locally by digest_html.py {VERSION} &mdash; pure stdlib, no network.</footer>
<script>
{_JS}</script>
</body>
</html>
"""


def build_demo_html(reference_date: datetime.date) -> str:
    """Render the synthetic all-five-lenses sample end to end: prose -> cited
    records -> the combined report -> a single HTML digest page."""
    from data.sample_records import DIGEST_SAMPLE_GAZETTEER, DIGEST_SAMPLE_NOTE

    records = extract_records(DIGEST_SAMPLE_NOTE, DIGEST_SAMPLE_GAZETTEER)
    reports = run_report(records)
    return render_digest(
        DIGEST_SAMPLE_NOTE, records, reports, reference_date=reference_date
    )


# ---------------------------------------------------------------------------
# Multi-patient rendering (ADR 0016 batch -> view). A batch note split by
# extract_records_multi yields several ACCEPTED patient records (each carrying a
# provenance.segment_span) plus QUARANTINED segments. We render one stacked block
# per accepted patient, IN SEGMENT ORDER (never reordered — the librarian rule),
# each with its OWN source segment so a click can only ever highlight within that
# patient (structural no cross-patient bleed); a compact patient index jumps
# between them; refused segments are surfaced in a neutral quarantine section,
# never merged or guessed. The index / quarantine / scoped-JS / per-segment note
# chrome is shared (view_html); this view supplies the card-idiom per-patient body.
# ---------------------------------------------------------------------------


def _render_patient_block(
    note: str, record: dict, report: RecordReport | None
) -> str:
    """One accepted patient: lens cards beside that patient's OWN cited segment,
    wrapped in an anchored section the patient index can jump to."""
    patient_id = record.get("id", "")
    cards_html = _render_cards([report] if report is not None else [])
    note_html = _localized_note(note, record)
    return (
        f'<section class="patient" id="{_esc(_anchor_id(patient_id))}">'
        f'<h2 class="patient-id">Patient {_esc(patient_id)}</h2>'
        '<div class="patient-body">'
        f'<div class="patient-patterns">{cards_html}</div>'
        f'<div class="patient-source"><div class="note">{note_html}</div></div>'
        "</div></section>"
    )


def render_digest_multi(
    note: str,
    result: MultiExtractResult,
    reports: list[RecordReport],
    *,
    title: str = "Pre-visit Pattern Digest",
    reference_date: datetime.date | None = None,
) -> str:
    """A single self-contained HTML document for a MULTI-patient batch: one stacked,
    anchored block per accepted patient (cards + that patient's own cited segment),
    a jump index, and a neutral quarantine section for refused segments. Patients
    stay in segment order; nothing is ranked, merged, or interpreted."""
    by_id = {rep.record_id: rep for rep in reports}
    index_html = _render_patient_index(result.records)
    if result.records:
        blocks = "\n".join(
            _render_patient_block(note, rec, by_id.get(rec.get("id", "")))
            for rec in result.records
        )
    else:
        blocks = '<p class="empty">No patient segments were accepted.</p>'
    quarantine_html = _render_quarantine(result.quarantined)
    meta_bits = [f"{len(result.records)} patients"]
    if result.quarantined:
        meta_bits.append(f"{len(result.quarantined)} quarantined")
    if reference_date is not None:
        meta_bits.append(f"Encounter {reference_date.isoformat()}")
    meta_bits.append("de-identified")
    meta = " &middot; ".join(_esc(b) for b in meta_bits)
    return f"""<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(title)}</title>
<style>
{_THEME_CSS}{_CSS}{_MULTI_CHROME_CSS}{_THEME_MEDIA_CSS}{_PRINT_CSS}</style>
<script>
{_THEME_JS}</script>
</head>
<body>
<header>
<button class="theme-toggle" type="button">Dark</button>
<h1>{_esc(title)}</h1>
<p class="meta">{meta}</p>
<p class="stance">Surfaced from each record and cited &mdash; never judged, ordered, or recommended.
Each patient's source stands alone. The clinician decides.</p>
</header>
{index_html}
<main class="patients">
{blocks}
</main>
{quarantine_html}
<footer>Health Prototype &middot; librarian layer &middot; synthetic data &middot;
generated locally by digest_html.py {VERSION} &mdash; pure stdlib, no network.</footer>
<script>
{_MULTI_JS}</script>
</body>
</html>
"""


def build_demo_multi_html(reference_date: datetime.date) -> str:
    """Render the synthetic multi-patient batch end to end: a batch note ->
    fail-closed split -> per-patient reports -> one stacked HTML digest with a
    quarantine section. Uses no per-patient shift (0, like the single demo) so the
    cited dates stay hand-readable against each segment."""
    from data.sample_records import FREETEXT_MULTI_DELIMITER, FREETEXT_MULTI_NOTE

    gazetteer = ["poor sleep", "headache"]
    result = extract_records_multi(
        FREETEXT_MULTI_NOTE, gazetteer, delimiter=FREETEXT_MULTI_DELIMITER
    )
    reports = run_report(result.records)
    return render_digest_multi(
        FREETEXT_MULTI_NOTE, result, reports, reference_date=reference_date
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render the clinician-facing Pre-visit Pattern Digest as a "
        "self-contained HTML file (lens cards + cited source). Pure stdlib; no "
        "network; no PHI.",
    )
    parser.add_argument(
        "--version", action="store_true", help="Print the version and exit"
    )
    parser.add_argument(
        "--demo",
        nargs="?",
        const="digest_demo.html",
        default=None,
        metavar="OUTFILE",
        help="Write the all-five-lenses sample digest to OUTFILE (default digest_demo.html)",
    )
    parser.add_argument(
        "--demo-multi",
        nargs="?",
        const="digest_multi_demo.html",
        default=None,
        metavar="OUTFILE",
        help="Write the multi-patient batch digest (stacked patients + quarantine) "
        "to OUTFILE (default digest_multi_demo.html)",
    )
    args = parser.parse_args()
    if args.version:
        print(f"Health-Prototype pre-visit digest {VERSION}")
        return 0
    if args.demo is not None:
        path = args.demo
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(build_demo_html(datetime.date(2026, 3, 15)))
        print(f"Wrote {path}")
        return 0
    if args.demo_multi is not None:
        path = args.demo_multi
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(build_demo_multi_html(datetime.date(2026, 3, 15)))
        print(f"Wrote {path}")
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
