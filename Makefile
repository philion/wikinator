.PHONY: all run clean

# Simple makefile to help me remember uv tasks
# Targets are:
# - lint     : run ruff linter
# - fix      : ... with fixes
# - test     : run test suite
# - build    : build
# - publish  : publish
# - dist     : clean, build, publish
# - clean    : remove anything built


lint:
	uvx ruff check

fix:
	uvx ruff check --fix

test:
	uv run pytest

build:
	uv build

dist:
	rm -fr dist/
	uv build
	uv publish

clean:
	rm -fr .ruff_cache/
	rm -fr dist/
	rm -f dpytest_*.dat
	find . -type f -name ‘*.pyc’ -delete
	find . -name __pycache__  | xargs rm -rf
