#!/usr/bin/env python3
"""view_html.py — shared, pure view primitives for the HTML views.

Pure stdlib. Zero external dependencies. This module is the dependency FLOOR for
the two views: it holds the one source of truth for the calm theme (CSS design
tokens), neutral span rendering, HTML-escaping, the click-to-highlight scripts,
and the multi-patient chrome (per-patient block frame, jump-index, quarantine).

`report_html.py` (inspection view) and `digest_html.py` (clinician digest) both
import FROM here; neither imports from the other (that would be circular). When a
third view surface arrived — multi-patient `report_html` (ADR 0021) — the shared
helpers were promoted out of `report_html`/`digest_html` into this module, exactly
the move ADR 0015 / 0017 pre-declared ("if a third view appears, promote them into
a small shared `view_html` module").

It imports NOTHING from the views or the engine — only stdlib `html` — so it can
never close an import cycle.
"""

from __future__ import annotations

import html

VERSION = "0.2.0"

# --- Shared calm theme (ADR 0017) -------------------------------------------
# One source of truth for colour, reused by both views so they can never drift
# apart. Tokens are CSS custom properties; each view's own CSS (layout)
# references them via var(). Light-first + an optional dark toggle. Colour is
# NON-semantic: a single accent marks interactivity/selection, the SAME for every
# lens — it never encodes severity, type, or judgment (the librarian rule, held
# in the view). Contrast is WCAG-checked in tests/test_view_theme.py, which
# imports THEME directly.
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
header { position: relative; padding: 22px 28px; padding-inline-end: 96px;
         border-block-end: 1px solid var(--border); background: var(--surface); }
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
.finding:focus-visible { outline: 2px solid var(--accent-line); outline-offset: 2px; }
.empty { color: var(--muted); font-size: 13px; }
footer { padding: 14px 28px; border-block-start: 1px solid var(--border);
         color: var(--muted); font-size: 12px; background: var(--surface); }
.theme-toggle { position: absolute; inset-block-start: 14px; inset-inline-end: 16px; z-index: 10;
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
  // Print pass (ADR 0022): CSS cannot set a <details> open state, so force every
  // collapsed cited-date list open while printing and restore it afterward, so the
  // full provenance prints (the _PRINT_CSS display rule is the no-JS fallback).
  window.addEventListener('beforeprint', function () {
    document.querySelectorAll('details').forEach(function (d) {
      d.dataset.wasOpen = d.open ? '1' : '0'; d.open = true;
    });
  });
  window.addEventListener('afterprint', function () {
    document.querySelectorAll('details').forEach(function (d) {
      if (d.dataset.wasOpen === '0') { d.open = false; }
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

# Print pass (ADR 0022), appended LAST in each view's <style> so it wins for print.
# A clinician hands a pre-visit page off on paper: single column, drop the on-screen
# chrome (toggle + footer), keep each cited mark legible in grayscale via a border
# (not colour — print-color-adjust is a best-effort extra, never relied on), keep a
# patient/card/finding from splitting across a page, and expand the collapsed
# cited-date lists so the FULL provenance prints (the beforeprint JS also forces the
# <details> open; this display rule is the no-JS fallback). Logical properties +
# break-inside keep the banned `top` token out (no page-break-*). A4/Letter via @page.
_PRINT_CSS = """\
@media print {
  :root { color-scheme: light; }
  .theme-toggle, footer { display: none; }
  main, .patient-body { display: block; }
  .note-col, .panel, .patterns, .source,
  .patient-patterns, .patient-source { inline-size: 100%; border-inline-end: none; }
  .patient, .card, li.finding { break-inside: avoid; }
  mark.cite { border: 1px solid currentColor; print-color-adjust: exact; }
  mark.cite.active { outline: 1px solid currentColor; }
  details > .cites-full { display: block; }
  @page { size: A4; margin: 14mm; }
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


# Shared click + KEYBOARD highlight (ADR 0022): one activation path for mouse and
# keyboard so a finding toggles its cited concept marks identically either way. The
# findings carry tabindex/role/aria-pressed in the static markup; this binds the
# listeners and reflects pressed state. `bindFindings(findings, marks)` is scoped by
# its caller — over the whole document (single view) or per `.patient` block (multi,
# so two patients sharing an item can never light up each other). The
# closest('details') guard keeps the cited-date disclosure from toggling the
# highlight (mouse OR keyboard); avoids the banned `top` token (block:'center').
_INTERACT_JS = """\
function bindFindings(findings, marks) {
  function clearMarks() { marks.forEach(function (m) { m.classList.remove('active'); }); }
  function activate(el) {
    var items = (el.getAttribute('data-items') || '').split('|').filter(Boolean);
    var turningOn = !el.classList.contains('sel');
    findings.forEach(function (o) { o.classList.remove('sel'); o.setAttribute('aria-pressed', 'false'); });
    clearMarks();
    if (!turningOn) { return; }
    el.classList.add('sel');
    el.setAttribute('aria-pressed', 'true');
    var first = null;
    marks.forEach(function (m) {
      if (items.indexOf(m.getAttribute('data-item')) >= 0) {
        m.classList.add('active');
        if (!first) { first = m; }
      }
    });
    if (first) { first.scrollIntoView({ block: 'center', behavior: 'smooth' }); }
  }
  findings.forEach(function (el) {
    el.addEventListener('click', function (e) {
      if (e.target.closest('details')) { return; }
      activate(el);
    });
    el.addEventListener('keydown', function (e) {
      if (e.target.closest('details')) { return; }
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); activate(el); }
    });
  });
}
"""

# Single-scope: bind every finding in the document (inspection view + single digest).
_JS = _INTERACT_JS + """\
(function () {
  bindFindings(document.querySelectorAll('.finding'), document.querySelectorAll('mark.cite'));
})();
"""

# ---------------------------------------------------------------------------
# Multi-patient chrome (ADR 0016 batch -> view; promoted here for ADR 0021 so
# BOTH views can render a batch). A batch note split by extract_records_multi
# yields several ACCEPTED patient records (each carrying a provenance.segment_span)
# plus QUARANTINED segments. The shared helpers below render one stacked block per
# accepted patient, IN SEGMENT ORDER (never reordered — the librarian rule), each
# with its OWN source segment so a click can only ever highlight within that patient
# (structural no cross-patient bleed); a compact patient index jumps between them;
# refused segments are surfaced in a neutral quarantine section, never merged or
# guessed. Each view supplies its own per-patient body (cards vs. findings list).
# ---------------------------------------------------------------------------

# Layout chrome for the multi view (colour/typography/.card/.chip/.note are shared;
# each view brings its own inner-content CSS via its _CSS). Used by both views.
_MULTI_CHROME_CSS = """\
.patient-index { padding: 12px 28px; border-block-end: 1px solid var(--border);
                 background: var(--surface); font-size: 13px; }
.index-label { color: var(--muted); margin-inline-end: 8px; }
.patient-index a { color: var(--accent); text-decoration: none; margin-inline-end: 12px;
                   white-space: nowrap; border-block-end: 1px dotted var(--accent-line); }
.patient { padding: 18px 28px; border-block-end: 1px solid var(--border); }
.patient-id { color: var(--text); font-size: 14px; text-transform: none; letter-spacing: 0;
              margin: 0 0 12px; }
.patient-body { display: flex; gap: 24px; align-items: flex-start; }
.patient-patterns { flex: 1 1 58%; }
.patient-source { flex: 1 1 42%; }
.quarantine { padding: 18px 28px; background: var(--surface); }
.quarantine ul { list-style: none; margin: 0; padding: 0; }
.quarantine li { font-size: 13px; color: var(--muted); padding: 6px 0;
                 border-block-end: 1px solid var(--border); }
.quarantine .seg { color: var(--text); font-weight: 600; margin-inline-end: 8px; }
@media (max-width: 640px) {
  .patient, .quarantine { padding: 14px 16px; }
  .patient-index { padding: 12px 16px; }
  .patient-body { flex-direction: column; gap: 14px; }
  .patient-patterns, .patient-source { flex: 0 0 auto; inline-size: 100%; }
}
"""

# Per-patient scope: bind each .patient block's findings to its OWN marks, so two
# patients sharing an item can never light up each other (the no-bleed guarantee,
# enforced in the view). Reuses the SAME bindFindings as the single view.
_MULTI_JS = _INTERACT_JS + """\
(function () {
  document.querySelectorAll('.patient').forEach(function (block) {
    bindFindings(block.querySelectorAll('.finding'), block.querySelectorAll('mark.cite'));
  });
})();
"""

# Neutral, non-interpretive labels for each fail-closed reason (ADR 0016). The
# engine's own reason code is shown too, so the wording adds nothing it didn't
# already classify — surfacing, not interpreting.
_QUARANTINE_LABELS = {
    "missing_key": "no patient identifier in segment",
    "ambiguous_key": "more than one patient identifier in segment",
    "duplicate_key": "patient identifier shared with another segment",
    "missing_shift": "no per-patient de-identification shift supplied",
}


def _anchor_id(patient_id: str) -> str:
    """A safe in-page anchor for a patient id (alnum kept, anything else -> '-')."""
    return "patient-" + "".join(c if c.isalnum() else "-" for c in patient_id)


def _localized_note(note: str, record: dict) -> str:
    """Render ONE patient's own source SEGMENT with segment-local marks.

    The segment text is sliced from the whole note via the record's
    ``provenance.segment_span``; the entries' whole-note spans are rebased to
    segment-local offsets, so each patient's note stands alone — a click can only
    ever highlight within this patient's own segment (no cross-patient bleed). A
    record without multi provenance falls back to the whole-note render."""
    prov = record.get("provenance") or {}
    seg_span = prov.get("segment_span")
    if not seg_span:
        return _render_note(note, _collect_spans([record]))
    start, end = seg_span
    segment = note[start:end]
    local = [
        (s - start, e - start, label, kind)
        for (s, e, label, kind) in _collect_spans([record])
    ]
    return _render_note(segment, local)


def _render_patient_index(records: list[dict]) -> str:
    """A compact jump-list to each accepted patient (anchor links, no JS state) so
    a clinician moves between patients without losing the single-page context. Only
    shown when there is more than one patient."""
    if len(records) <= 1:
        return ""
    links = " ".join(
        f'<a href="#{_esc(_anchor_id(r.get("id", "")))}">{_esc(r.get("id", ""))}</a>'
        for r in records
    )
    return (
        '<nav class="patient-index">'
        '<span class="index-label">Patients in this batch:</span> '
        f"{links}</nav>"
    )


def _render_quarantine(quarantined: list) -> str:
    """The refused segments, surfaced in segment order with their neutral reason —
    never merged, guessed, or interpreted. Empty -> nothing (no 'all clean' claim)."""
    if not quarantined:
        return ""
    rows = []
    for q in quarantined:
        label = _QUARANTINE_LABELS.get(q.reason, q.reason)
        detail = f" &mdash; {_esc(q.detail)}" if getattr(q, "detail", "") else ""
        rows.append(
            f'<li><span class="seg">Segment {q.index}</span>'
            f"{_esc(label)} ({_esc(q.reason)}){detail}</li>"
        )
    return (
        '<section class="quarantine">'
        "<h2>Quarantined segments (not rendered as patients)</h2>"
        f'<ul>{"".join(rows)}</ul></section>'
    )
