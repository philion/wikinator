# Simple makefile to help me remember uv tasks
# Targets are:
# - lint     : run ruff linter
# - fix      : ... with fixes
# - test     : run test suite
# - build    : build
# - release  : Bump the version, update metadata, tag the release
# - dist     : clean, build, publish
# - clean    : remove anything built

# load vars from .env
# specifically, UV_PUBLISH_TOKEN for "make publish"
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

.PHONY: all run clean

lint:
	uvx ruff check

fix:
	uvx ruff check --fix

test:
	uv run pytest --log-cli-level=DEBUG

build:
	uv build

release:
	uv version --bump patch
	git tag -a v$(shell uv version --short) -m "Version $(shell uv version)"
	git commit -am "Releasing $(shell uv version)"
	git push

dist:
	rm -fr dist/
	uv build
	uv publish

clean:
	rm -fr .ruff_cache/
	rm -fr dist/
	rm -fr .venv/
	rm -f dpytest_*.dat
	rm -fr .pytest_cache/
	find . -type f -name '*.pyc' -delete
	find . -name __pycache__  | xargs rm -rf
