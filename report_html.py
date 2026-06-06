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

# --- Shared calm theme (ADR 0017) -------------------------------------------
# One source of truth for colour, reused by digest_html so the two views can
# never drift apart. Tokens are CSS custom properties; each view's own CSS
# (layout) references them via var(). Light-first + an optional dark toggle.
# Colour is NON-semantic: a single accent marks interactivity/selection, the
# SAME for every lens — it never encodes severity, type, or judgment (the
# librarian rule, held in the view). Contrast is WCAG-checked in
# tests/test_view_theme.py, which imports THEME directly.
THEME = {
    "light": {
        "bg": "#FAF6FB", "surface": "#FFFDFF", "text": "#291E2E",
        "muted": "#675A6E", "border": "#E6DDEA", "mark-rest": "#F1E8F4",
        "accent": "#7A3A86", "accent-weak": "#F0E1F4", "accent-line": "#8A4F96",
    },
    "dark": {
        "bg": "#221026", "surface": "#2C1730", "text": "#ECE4EF",
        "muted": "#B4A3B8", "border": "#3E2A44", "mark-rest": "#34203A",
        "accent": "#D7A0DE", "accent-weak": "#3C2244", "accent-line": "#B074BA",
    },
}


def _root_block(selector: str, tokens: dict[str, str], scheme: str) -> str:
    """One CSS rule mapping the theme tokens to custom properties (var())."""
    decls = "".join(f"--{k}: {v}; " for k, v in tokens.items())
    return f"{selector} {{ color-scheme: {scheme}; {decls}}}\n"


# Tokens (light + dark) plus the components both views share: base typography,
# the cited note + neutral marks, the lens label, header/footer, the dark toggle.
# Layout (the two-column split, cards vs. list) stays in each view's own _CSS.
_THEME_CSS = (
    _root_block(":root", THEME["light"], "light")
    + _root_block(':root[data-theme="dark"]', THEME["dark"], "dark")
    + """\
* { box-sizing: border-box; }
body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
       margin: 0; color: var(--text); background: var(--bg); line-height: 1.5; }
header { padding: 22px 28px; border-block-end: 1px solid var(--border); background: var(--surface); }
header h1 { font-size: 22px; margin: 0; font-weight: 600; letter-spacing: -.01em; }
.meta { margin: 6px 0 0; color: var(--muted); font-size: 13px; }
.stance { margin: 8px 0 0; color: var(--muted); font-size: 13px; max-width: 80ch; }
h2 { font-size: 12px; text-transform: uppercase; letter-spacing: .05em;
     color: var(--muted); margin: 0 0 14px; font-weight: 600; }
.note { white-space: pre-wrap; font-family: ui-monospace, Menlo, Consolas, monospace;
        font-size: 13px; background: var(--surface); border: 1px solid var(--border);
        border-radius: 8px; padding: 14px; color: var(--text); }
mark.cite { background: var(--mark-rest); border-radius: 3px; padding: 0 2px; color: inherit; }
mark.cite-date { background: transparent; border-block-end: 1px dotted var(--accent-line); }
mark.cite.active { background: var(--accent-weak); outline: 2px solid var(--accent-line); outline-offset: 1px; }
.lens { color: var(--accent); font-weight: 700; letter-spacing: .06em; text-transform: uppercase; }
.finding { cursor: pointer; }
.empty { color: var(--muted); font-size: 13px; }
footer { padding: 14px 28px; border-block-start: 1px solid var(--border);
         color: var(--muted); font-size: 12px; background: var(--surface); }
.theme-toggle { position: fixed; inset-block-start: 14px; inset-inline-end: 16px; z-index: 10;
                background: var(--surface); color: var(--text); border: 1px solid var(--border);
                border-radius: 999px; padding: 6px 14px; font-size: 13px; cursor: pointer; }
.theme-toggle:hover { border-color: var(--accent-line); }
"""
)

# Sets the initial theme from the OS preference (no flash), then wires the toggle.
_THEME_JS = """\
(function () {
  var root = document.documentElement;
  var mq = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)');
  root.setAttribute('data-theme', mq && mq.matches ? 'dark' : 'light');
  document.addEventListener('DOMContentLoaded', function () {
    var btn = document.querySelector('.theme-toggle');
    if (!btn) { return; }
    function label() { btn.textContent = root.getAttribute('data-theme') === 'dark' ? 'Light' : 'Dark'; }
    label();
    btn.addEventListener('click', function () {
      root.setAttribute('data-theme', root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
      label();
    });
  });
})();
"""

# Android-targeted responsive layer (ADR 0018), appended LAST in each view's <style>
# so it overrides the shared base + the view's own layout. Primary width 360 px (the
# most common Android viewport, incl. Galaxy S25 = 360x780 CSS); below 640 px (every
# Android phone portrait) the two columns stack and spacing/tap targets adapt; foldable
# unfolded (~768) + tablets keep the two-column layout. Pure CSS — no JS change, no deps.
# Logical properties keep `top` out of the document (banned-words rule).
_THEME_MEDIA_CSS = """\
@media (max-width: 640px) {
  main { flex-direction: column; }
  main > section { flex: 0 0 auto; border-inline-end: none; padding: 14px 16px; }
  main > section:not(:last-child) { border-block-end: 1px solid var(--border); }
  header { padding: 16px 16px; padding-inline-end: 84px; }
  .note { overflow-x: auto; }
  .card, li.finding { padding: 14px 14px; }
  .theme-toggle { inset-block-start: 12px; inset-inline-end: 12px;
                  padding: 10px 16px; min-block-size: 44px; }
}
"""


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
li.finding { padding: 7px 9px; border: 1px solid var(--border); border-radius: 6px;
             margin: 0 0 6px; background: var(--surface); font-size: 13px; }
li.finding:hover { border-color: var(--accent-line); }
li.finding.sel { border-color: var(--accent); box-shadow: 0 0 0 2px var(--accent-weak); }
.lens { display: inline-block; min-width: 9ch; font-size: 11px; margin-inline-end: 8px; }
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
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(title)}</title>
<style>
{_THEME_CSS}{_CSS}{_THEME_MEDIA_CSS}</style>
<script>
{_THEME_JS}</script>
</head>
<body>
<button class="theme-toggle" type="button">Dark</button>
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
