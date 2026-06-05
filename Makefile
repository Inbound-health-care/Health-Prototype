.PHONY: test selftest demo lint check typecheck fmt-check fmt cov security tools branch-audit clean

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

lint:          ## Byte-compile sanity check (+ ruff if installed)
	python -m compileall -q recurrence.py extract.py tests data scripts
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

tools:         ## Report which optional dev tools are available
	@for t in python3 pytest ruff mypy pyright uv black; do \
	  printf "%-9s" "$$t"; command -v "$$t" >/dev/null 2>&1 && command -v "$$t" || echo MISSING; \
	done
	@echo "on-demand via uvx (no install): coverage  bandit  ty  pre-commit"

branch-audit:  ## Read-only audit of local/remote branch cleanup candidates
	python scripts/branch_audit.py

clean:         ## Remove caches
	rm -rf __pycache__ */__pycache__ */*/__pycache__ .ruff_cache
