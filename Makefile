.PHONY: test selftest demo compile lint check typecheck fmt-check fmt cov security proptest jstest html-demos tools branch-audit clean

# Engine is pure stdlib; no runtime dependencies to install.
# The targets below test/lint/type-check are OPTIONAL dev tooling: each is a
# no-op when the tool is absent, or reaches it via `uvx`. None is imported by
# the engine. See docs/TOOLCHAIN_AUDIT_2026-05-31.md.

test:          ## Run the full unittest suite
	python -m unittest discover -s tests -t .

selftest:      ## Run the six required engine spec cases + the extractor self-test
	python recurrence.py --self-test
	python extract.py --self-test

demo:          ## Run every surfacing-rule demo
	python recurrence.py --demo
	python recurrence.py --demo-v1
	python recurrence.py --demo-gap
	python recurrence.py --demo-frequency
	python recurrence.py --demo-cooccurrence

compile:       ## Byte-compile every project file (syntax gate; THE canonical file list)
	python -m compileall -q recurrence.py extract.py view_html.py report_html.py digest_html.py tests data scripts

lint:          ## compile + ruff (if installed). CI delegates here so the file list lives once.
	$(MAKE) compile
	-ruff check .

check:         ## Standard local verification gate: tests + self-test + lint
	$(MAKE) test
	$(MAKE) selftest
	$(MAKE) lint

typecheck:     ## Static type check (mypy if installed) — report-only, won't fail the run
	-mypy recurrence.py

fmt-check:     ## Show what `ruff format` WOULD change (non-destructive)
	-ruff format --check .

fmt:           ## Apply `ruff format` (cosmetic; large diff — opt-in, see toolchain audit)
	ruff format .

cov:           ## Test coverage via uvx (no install): run suite + report
	-uvx coverage run -m pytest -q && uvx coverage report

security:      ## Security/AST lint via uvx (no install)
	-uvx bandit -q -r recurrence.py

# Property tests are dev-only/additive: the suite SKIPS them when hypothesis is
# absent, so `make test` stays pure-stdlib green. `make proptest` runs them via uvx.
# CI ALSO gates them now (ADR 0025, 0027) — it installs hypothesis and runs these
# modules derandomized: the fail-closed EXTRACTOR invariants and the rule-layer
# metamorphic properties protect every PR (no longer a bare skip).
proptest:      ## Property-based tests (Hypothesis via uvx; no install)
	-uvx --with hypothesis python -m unittest tests.test_extract_multi_properties tests.test_rule_properties -v

# Live JS/DOM test (ADR 0025): executes the views' interactive JS in headless
# Chromium so a runtime bug can't pass as a green static-string assert. Dev-only,
# NOT in CI (browser binaries are heavy); SKIPS cleanly when Playwright/Chromium is
# absent. First run only: `uvx --with playwright playwright install chromium`.
jstest:        ## Live JS/DOM view test (Playwright via uvx; no install)
	-uvx --with playwright python -m unittest tests.test_view_js -v

# Generate the four self-contained views for the CI HTML-validity gate (ADR 0026).
# Pure stdlib, deterministic. CI's `html` job calls this, then runs proof-html on _site/,
# so the four-file list lives here once (CI<->Makefile parity, like `compile`).
html-demos:    ## Generate the four self-contained HTML views into _site/ (the proof-html input; CI delegates here)
	mkdir -p _site
	python report_html.py --demo       _site/report_demo.html
	python report_html.py --demo-multi _site/report_multi_demo.html
	python digest_html.py --demo       _site/digest_demo.html
	python digest_html.py --demo-multi _site/digest_multi_demo.html

tools:         ## Report which optional dev tools are available
	@for t in python3 pytest ruff mypy pyright uv black; do \
	  printf "%-9s" "$$t"; command -v "$$t" >/dev/null 2>&1 && command -v "$$t" || echo MISSING; \
	done
	@echo "on-demand via uvx (no install): coverage  bandit  ty  pre-commit"

branch-audit:  ## Read-only audit of local/remote branch cleanup candidates
	python scripts/branch_audit.py

clean:         ## Remove caches
	rm -rf __pycache__ */__pycache__ */*/__pycache__ .ruff_cache
