#!/usr/bin/env python3
"""report_html.py — self-contained HTML view of the librarian's output (UI slice 1).

Pure stdlib. Zero external dependencies. Local-only (no network egress): the output
is a SINGLE self-contained .html file (inline CSS/JS, no CDN, no external src), so it
opens offline and can be handed to a reviewer as-is.

It renders the provenance the engine already produces — the source note with each
cited span highlighted (extract.py's source_span, and the cited temporal phrase from
ADR 0013's relative-date pass) beside the patterns the five rules surface
(recurrence.py's run_report). Clicking a surfaced pattern highlights its cited spans
in the note: "every line traces to source" made visible — i.e. FDA Non-Device CDS
criterion 4 (the basis is reviewable) on screen.

It honors the librarian rule in the VIEW layer too: a calm, low-stimulation theme with a
single NON-semantic accent (the same for every lens — no per-lens or severity colors),
light-first with an optional dark toggle, document order only — it surfaces and cites,
it does NOT rank, score, flag, judge, or interpret. See ADR 0014 (view) + ADR 0017 (theme).

The shared theme + neutral-span helpers live in view_html.py (the dependency floor,
ADR 0021); this module keeps only the inspection layout and renders both a single-note
report and a multi-patient batch (stacked, per-patient-scoped — mirrors the digest).

  Demo:        python report_html.py --demo [outfile.html]
  Multi-batch: python report_html.py --demo-multi [outfile.html]
"""

from __future__ import annotations

import argparse
import datetime
import sys

from extract import MultiExtractResult, extract_records, extract_records_multi
from recurrence import RecordReport, run_report

# Shared, pure view primitives — one source of truth for the calm theme, span
# collection, neutral <mark> rendering, HTML-escaping, the click-to-highlight
# scripts, and the multi-patient chrome (jump-index, quarantine, per-patient
# scoped JS), so the inspection view and the digest can never drift apart.
# THEME is re-exported here for back-compat (tests/test_view_theme.py imports it
# from report_html).
from view_html import (
    THEME,
    _JS,
    _MULTI_CHROME_CSS,
    _MULTI_JS,
    _PRINT_CSS,
    _THEME_CSS,
    _THEME_JS,
    _THEME_MEDIA_CSS,
    _TIMELINE_CSS,
    _anchor_id,
    _collect_spans,
    _esc,
    _localized_note,
    _render_note,
    _render_patient_index,
    _render_quarantine,
    _render_timeline,
    _timeline_rows,
)

__all__ = ["THEME", "render_html", "render_html_multi", "build_demo_html"]

VERSION = "0.5.0"


def _hit_items(hit: object) -> list[str]:
    """The item label(s) a finding cites, for linking to note marks (co-occurrence
    carries two)."""
    items: list[str] = []
    for attr in ("item", "item_a", "item_b"):
        value = getattr(hit, attr, None)
        if value:
            items.append(value)
    return items


def _render_findings_list(report: RecordReport | None) -> str:
    """One record's surfaced patterns as a ``<ul>`` of findings (no record header —
    the caller supplies the surrounding heading). Each row keeps its lens
    (provenance) and the engine's own neutral line, plus the cited item(s) as a data
    attribute so a click can highlight the source. A record that surfaced nothing
    renders the neutral note; it never asserts 'clean'."""
    findings = report.findings if report is not None else []
    if not findings:
        return '<p class="empty">No patterns surfaced. (The record is not asserted clean.)</p>'
    rows = ['<ul class="findings">']
    for finding in findings:
        items = "|".join(_hit_items(finding.hit))
        rows.append(
            '<li><button type="button" class="finding" '
            f'data-items="{_esc(items)}" aria-pressed="false">'
            f'<span class="lens">{_esc(finding.expert)}</span>'
            f'<span class="line">{_esc(finding.line)}</span></button></li>'
        )
    rows.append("</ul>")
    return "\n".join(rows)


def _render_findings(reports: list[RecordReport]) -> str:
    """The surfaced patterns, grouped by record in registry order, each under its
    record header. No ordering by importance — there is none to assert."""
    if not reports:
        return '<p class="empty">No patterns surfaced. (The record is not asserted clean.)</p>'
    blocks: list[str] = []
    for report in reports:
        blocks.append(
            f"<h3>Record {_esc(report.record_id)}</h3>\n{_render_findings_list(report)}"
        )
    return "\n".join(blocks)


# Layout only — colour/typography/components live in _THEME_CSS (shared).
_CSS = """\
main { display: flex; gap: 0; align-items: stretch; }
section { padding: 16px 24px; }
header { padding: 16px 24px; }
header h1 { font-size: 18px; margin: 0 0 4px; }
.stance { max-width: 70ch; }
.note-col { flex: 1 1 55%; border-inline-end: 1px solid var(--border); }
.panel { flex: 1 1 45%; }
h3 { font-size: 13px; margin: 16px 0 6px; color: var(--text); }
ul.findings { list-style: none; margin: 0 0 8px; padding: 0; }
ul.findings > li { margin: 0 0 6px; }
.findings .finding { padding: 7px 9px; border: 1px solid var(--border); border-radius: 6px;
                     background: var(--surface); font-size: 13px; }
.findings .finding:hover { border-color: var(--accent-line); }
.findings .finding.sel { border-color: var(--accent); box-shadow: 0 0 0 2px var(--accent-weak); }
.lens { display: inline-block; min-width: 9ch; font-size: 11px; margin-inline-end: 8px; }
"""


def render_html(
    note: str,
    records: list[dict],
    reports: list[RecordReport],
    *,
    title: str = "Pattern Inspection Report",
    reference_date: datetime.date | None = None,
) -> str:
    """A single self-contained HTML document: the source note with cited spans
    highlighted beside the surfaced patterns, linked by a click. Pure string
    templating — no external resources, no network. Surfaces and cites; it does not
    judge, order, or recommend."""
    note_html = _render_note(note, _collect_spans(records))
    findings_html = _render_findings(reports)
    timeline_html = _render_timeline(
        _timeline_rows([f for rep in reports for f in rep.findings])
    )
    ids = ", ".join(_esc(r["id"]) for r in records if r.get("id"))
    meta_bits = []
    if ids:
        meta_bits.append(f"Record(s): {ids}")
    if reference_date is not None:
        meta_bits.append(f"Reference date: {_esc(reference_date.isoformat())}")
    meta = f'<p class="meta">{" &middot; ".join(meta_bits)}</p>' if meta_bits else ""
    return f"""<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(title)}</title>
<style>
{_THEME_CSS}{_CSS}{_TIMELINE_CSS}{_THEME_MEDIA_CSS}{_PRINT_CSS}</style>
<script>
{_THEME_JS}</script>
</head>
<body>
<header>
<button class="theme-toggle" type="button">Dark</button>
<h1>{_esc(title)}</h1>
<p class="stance">Surfaced from the record and cited &mdash; never judged, ordered, or recommended.
Verify each surfaced line against its highlighted source.</p>
{meta}
</header>
{timeline_html}
<main>
<section class="note-col">
<h2>Source note (cited spans highlighted)</h2>
<div class="note">{note_html}</div>
</section>
<section class="panel">
<h2>Surfaced patterns (click a line to highlight its source)</h2>
{findings_html}
</section>
</main>
<footer>Generated locally by report_html.py {VERSION} &mdash; pure stdlib, no network, synthetic data only.</footer>
<script>
{_JS}</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Multi-patient rendering (ADR 0021): the inspection view, brought to parity with
# the digest (ADR 0020). A batch note split by extract_records_multi yields several
# ACCEPTED patient records (each with a provenance.segment_span) plus QUARANTINED
# segments. One stacked block per accepted patient, IN SEGMENT ORDER (never
# reordered — the librarian rule), each with its OWN cited segment so a click can
# only highlight within that patient (structural no cross-patient bleed); the shared
# _MULTI_JS scopes findings<->marks per .patient block. The patient index + the
# quarantine section reuse the shared view_html chrome. The per-patient body is the
# inspection idiom (a findings LIST, not the digest's cards).
# ---------------------------------------------------------------------------


def _render_patient_block(
    note: str, record: dict, report: RecordReport | None
) -> str:
    """One accepted patient: the surfaced findings list beside that patient's OWN
    cited segment, wrapped in an anchored section the patient index can jump to."""
    patient_id = record.get("id", "")
    findings_html = _render_findings_list(report)
    note_html = _localized_note(note, record)
    timeline_html = _render_timeline(
        _timeline_rows(report.findings if report is not None else [])
    )
    return (
        f'<section class="patient" id="{_esc(_anchor_id(patient_id))}">'
        f'<h2 class="patient-id">Patient {_esc(patient_id)}</h2>'
        f"{timeline_html}"
        '<div class="patient-body">'
        f'<div class="patient-patterns">{findings_html}</div>'
        f'<div class="patient-source"><div class="note">{note_html}</div></div>'
        "</div></section>"
    )


def render_html_multi(
    note: str,
    result: MultiExtractResult,
    reports: list[RecordReport],
    *,
    title: str = "Pattern Inspection Report",
    reference_date: datetime.date | None = None,
) -> str:
    """A single self-contained HTML document for a MULTI-patient batch: one stacked,
    anchored block per accepted patient (findings list + that patient's own cited
    segment), a jump index, and a neutral quarantine section for refused segments.
    Patients stay in segment order; nothing is ranked, merged, or interpreted."""
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
        meta_bits.append(f"Reference date: {reference_date.isoformat()}")
    meta_bits.append("de-identified")
    meta = " &middot; ".join(_esc(b) for b in meta_bits)
    return f"""<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(title)}</title>
<style>
{_THEME_CSS}{_CSS}{_MULTI_CHROME_CSS}{_TIMELINE_CSS}{_THEME_MEDIA_CSS}{_PRINT_CSS}</style>
<script>
{_THEME_JS}</script>
</head>
<body>
<header>
<button class="theme-toggle" type="button">Dark</button>
<h1>{_esc(title)}</h1>
<p class="meta">{meta}</p>
<p class="stance">Surfaced from each record and cited &mdash; never judged, ordered, or recommended.
Each patient's source stands alone; verify each surfaced line against its highlighted source.</p>
</header>
{index_html}
<main class="patients">
{blocks}
</main>
{quarantine_html}
<footer>Generated locally by report_html.py {VERSION} &mdash; pure stdlib, no network, synthetic data only.</footer>
<script>
{_MULTI_JS}</script>
</body>
</html>
"""


def build_demo_html(reference_date: datetime.date) -> str:
    """Render the relative-date sample end to end: prose -> cited records -> the
    combined report -> a single HTML page (shows item AND cited-date spans)."""
    from data.sample_records import FREETEXT_GAZETTEER, FREETEXT_RELATIVE_NOTE

    records = extract_records(
        FREETEXT_RELATIVE_NOTE,
        FREETEXT_GAZETTEER,
        resolve_relative=True,
        reference_date=reference_date,
    )
    reports = run_report(records)
    return render_html(
        FREETEXT_RELATIVE_NOTE, records, reports, reference_date=reference_date
    )


def build_demo_multi_html(reference_date: datetime.date) -> str:
    """Render the synthetic multi-patient batch end to end: a batch note ->
    fail-closed split -> per-patient reports -> one stacked inspection page with a
    quarantine section. Uses no per-patient shift (0, like the single demo) so the
    cited dates stay hand-readable against each segment."""
    from data.sample_records import FREETEXT_MULTI_DELIMITER, FREETEXT_MULTI_NOTE

    gazetteer = ["poor sleep", "headache"]
    result = extract_records_multi(
        FREETEXT_MULTI_NOTE, gazetteer, delimiter=FREETEXT_MULTI_DELIMITER
    )
    reports = run_report(result.records)
    return render_html_multi(
        FREETEXT_MULTI_NOTE, result, reports, reference_date=reference_date
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render a self-contained HTML view of the librarian's output "
        "(cited spans + surfaced patterns). Pure stdlib; no network; no PHI.",
    )
    parser.add_argument(
        "--version", action="store_true", help="Print the version and exit"
    )
    parser.add_argument(
        "--demo",
        nargs="?",
        const="report_demo.html",
        default=None,
        metavar="OUTFILE",
        help="Write the relative-date sample report to OUTFILE (default report_demo.html)",
    )
    parser.add_argument(
        "--demo-multi",
        nargs="?",
        const="report_multi_demo.html",
        default=None,
        metavar="OUTFILE",
        help="Write the multi-patient batch report (stacked patients + quarantine) "
        "to OUTFILE (default report_multi_demo.html)",
    )
    args = parser.parse_args()
    if args.version:
        print(f"Health-Prototype HTML report {VERSION}")
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
