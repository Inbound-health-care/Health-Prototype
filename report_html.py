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

It honors the librarian rule in the VIEW layer too: neutral, grayscale-only highlights
(no severity colors), document order only — it surfaces and cites, it does NOT rank,
score, flag, judge, or interpret. See ADR 0014.

  Demo:  python report_html.py --demo [outfile.html]
"""

from __future__ import annotations

import argparse
import datetime
import html
import sys

from extract import extract_records
from recurrence import RecordReport, run_report

VERSION = "0.1.0"


def _esc(s: str) -> str:
    """HTML-escape for both text and attribute contexts (quotes included)."""
    return html.escape(str(s), quote=True)


def _collect_spans(records: list[dict]) -> list[tuple[int, int, str, str]]:
    """All highlightable spans across records' entries as ``(start, end, label, kind)``
    sorted by start. kind 'item' = a cited gazetteer hit (``source_span``); kind 'date'
    = a cited relative/partial/frequency phrase (``date_span``, ADR 0013). Spans are
    disjoint by construction (item spans never overlap; a date phrase precedes its
    line's content)."""
    spans: list[tuple[int, int, str, str]] = []
    for record in records:
        for entry in record.get("entries", []):
            source_span = entry.get("source_span")
            if source_span is not None:
                spans.append(
                    (source_span[0], source_span[1], entry.get("item", ""), "item")
                )
            date_span = entry.get("date_span")
            if date_span is not None:
                spans.append(
                    (date_span[0], date_span[1], entry.get("date_phrase", ""), "date")
                )
    spans.sort(key=lambda s: (s[0], s[1]))
    return spans


def _render_note(note: str, spans: list[tuple[int, int, str, str]]) -> str:
    """The note as HTML with each span wrapped in a neutral ``<mark>``. Text is
    HTML-escaped; spans are disjoint and sorted; any unexpected overlap is skipped
    (never raises). ``data-item`` lets a finding light up its cited concept spans."""
    out: list[str] = []
    cursor = 0
    for start, end, label, kind in spans:
        if start < cursor or start > len(note):
            continue
        out.append(_esc(note[cursor:start]))
        out.append(
            f'<mark class="cite cite-{kind}" data-item="{_esc(label)}" '
            f'title="{kind}: {_esc(label)}">{_esc(note[start:end])}</mark>'
        )
        cursor = end
    out.append(_esc(note[cursor:]))
    return "".join(out)


def _hit_items(hit: object) -> list[str]:
    """The item label(s) a finding cites, for linking to note marks (co-occurrence
    carries two)."""
    items: list[str] = []
    for attr in ("item", "item_a", "item_b"):
        value = getattr(hit, attr, None)
        if value:
            items.append(value)
    return items


def _render_findings(reports: list[RecordReport]) -> str:
    """The surfaced patterns, grouped by record in registry order. Each row keeps its
    lens (provenance) and the engine's own neutral line, plus the cited item(s) as a
    data attribute so a click can highlight the source. No ordering by importance —
    there is none to assert."""
    if not reports:
        return '<p class="empty">No patterns surfaced. (The record is not asserted clean.)</p>'
    blocks: list[str] = []
    for report in reports:
        rows = [f"<h3>Record {_esc(report.record_id)}</h3>", '<ul class="findings">']
        for finding in report.findings:
            items = "|".join(_hit_items(finding.hit))
            rows.append(
                f'<li class="finding" data-items="{_esc(items)}">'
                f'<span class="lens">{_esc(finding.expert)}</span>'
                f'<span class="line">{_esc(finding.line)}</span></li>'
            )
        rows.append("</ul>")
        blocks.append("\n".join(rows))
    return "\n".join(blocks)


_CSS = """\
:root { color-scheme: light; }
* { box-sizing: border-box; }
body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
       margin: 0; color: #1a1a1a; background: #fafafa; line-height: 1.5; }
header { padding: 16px 24px; border-bottom: 1px solid #ddd; background: #fff; }
header h1 { font-size: 18px; margin: 0 0 4px; font-weight: 600; }
.stance { margin: 4px 0 0; color: #555; font-size: 13px; max-width: 70ch; }
.meta { margin: 6px 0 0; color: #777; font-size: 12px; }
main { display: flex; gap: 0; align-items: stretch; }
section { padding: 16px 24px; }
.note-col { flex: 1 1 55%; border-right: 1px solid #eee; }
.panel { flex: 1 1 45%; }
h2 { font-size: 13px; text-transform: uppercase; letter-spacing: .04em;
     color: #666; margin: 0 0 12px; font-weight: 600; }
h3 { font-size: 13px; margin: 16px 0 6px; color: #333; }
.note { white-space: pre-wrap; font-family: ui-monospace, Menlo, Consolas, monospace;
        font-size: 13px; background: #fff; border: 1px solid #eee; border-radius: 6px;
        padding: 14px; }
mark.cite { background: #ececec; border-radius: 2px; padding: 0 1px; cursor: default; }
mark.cite-date { background: transparent; border-bottom: 1px dotted #999; }
mark.cite.active { background: #cfcfcf; outline: 1px solid #8a8a8a; }
ul.findings { list-style: none; margin: 0 0 8px; padding: 0; }
li.finding { padding: 7px 9px; border: 1px solid #eee; border-radius: 6px;
             margin: 0 0 6px; background: #fff; cursor: pointer; font-size: 13px; }
li.finding.sel { border-color: #8a8a8a; background: #f0f0f0; }
.lens { display: inline-block; min-width: 9ch; color: #777; font-size: 11px;
        text-transform: uppercase; letter-spacing: .03em; margin-right: 8px; }
.empty { color: #777; font-size: 13px; }
footer { padding: 12px 24px; border-block-start: 1px solid #ddd; color: #888;
         font-size: 12px; background: #fff; }
"""

_JS = """\
(function () {
  var findings = document.querySelectorAll('.finding');
  var marks = document.querySelectorAll('mark.cite');
  function clearMarks() { marks.forEach(function (m) { m.classList.remove('active'); }); }
  findings.forEach(function (el) {
    el.addEventListener('click', function () {
      var items = (el.getAttribute('data-items') || '').split('|').filter(Boolean);
      var turningOn = !el.classList.contains('sel');
      findings.forEach(function (o) { o.classList.remove('sel'); });
      clearMarks();
      if (!turningOn) { return; }
      el.classList.add('sel');
      var first = null;
      marks.forEach(function (m) {
        if (items.indexOf(m.getAttribute('data-item')) >= 0) {
          m.classList.add('active');
          if (!first) { first = m; }
        }
      });
      if (first) { first.scrollIntoView({ block: 'center', behavior: 'smooth' }); }
    });
  });
})();
"""


def render_html(
    note: str,
    records: list[dict],
    reports: list[RecordReport],
    *,
    title: str = "Pattern digest",
    reference_date: datetime.date | None = None,
) -> str:
    """A single self-contained HTML document: the source note with cited spans
    highlighted beside the surfaced patterns, linked by a click. Pure string
    templating — no external resources, no network. Surfaces and cites; it does not
    judge, order, or recommend."""
    note_html = _render_note(note, _collect_spans(records))
    findings_html = _render_findings(reports)
    ids = ", ".join(_esc(r["id"]) for r in records if r.get("id"))
    meta_bits = []
    if ids:
        meta_bits.append(f"Record(s): {ids}")
    if reference_date is not None:
        meta_bits.append(f"Reference date: {_esc(reference_date.isoformat())}")
    meta = f'<p class="meta">{" &middot; ".join(meta_bits)}</p>' if meta_bits else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(title)}</title>
<style>
{_CSS}</style>
</head>
<body>
<header>
<h1>{_esc(title)}</h1>
<p class="stance">Surfaced from the record and cited &mdash; never judged, ordered, or recommended.
Verify each surfaced line against its highlighted source.</p>
{meta}
</header>
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
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
