.PHONY: test selftest demo lint clean

# Pure stdlib; no dependencies to install.

test:          ## Run the full unittest suite
	python -m unittest discover -s tests -t .

selftest:      ## Run the six required spec cases
	python recurrence.py --self-test

demo:          ## Run every surfacing-rule demo
	python recurrence.py --demo
	python recurrence.py --demo-v1
	python recurrence.py --demo-gap
	python recurrence.py --demo-frequency
	python recurrence.py --demo-cooccurrence

lint:          ## Byte-compile sanity check (+ ruff if installed)
	python -m compileall -q recurrence.py tests data
	-ruff check .

clean:         ## Remove caches
	rm -rf __pycache__ */__pycache__ */*/__pycache__ .ruff_cache
