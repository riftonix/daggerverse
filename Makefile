SHELL := /bin/sh

COMPONENT_KINDS := module scenario
COMPONENT_ROOT.module := modules
COMPONENT_ROOT.scenario := scenarios
COMPONENT_ROOTS := $(foreach kind,$(COMPONENT_KINDS),$(COMPONENT_ROOT.$(kind)))
COMPONENT_NAMES := $(foreach root,$(COMPONENT_ROOTS),$(notdir $(wildcard $(root)/*)))
COMMAND_TARGETS := help lint lint-check format format-check openspec-validate check-dagger-version release check-release-tag tests check-python-component check-test-component $(COMPONENT_KINDS)
COMMAND_ARGS := $(filter-out $(COMMAND_TARGETS),$(MAKECMDGOALS))
COMPONENT_KIND := $(filter $(COMPONENT_KINDS),$(MAKECMDGOALS))
QUALITY_GOAL := $(firstword $(filter lint lint-check format format-check,$(MAKECMDGOALS)))
PY_COMPONENT_ROOTS := $(foreach root,$(COMPONENT_ROOTS),$(wildcard $(root)/*))

RUFF ?= ruff
RUFF_FLAGS ?= --no-cache
OPENSPEC ?= openspec
DAGGER_ENV ?= DAGGER_NO_NAG=1 DO_NOT_TRACK=1 DAGGER_NO_UPDATE_CHECK=1

ifneq ($(strip $(COMMAND_ARGS)),)
SELECTED_ARG := $(firstword $(COMMAND_ARGS))
endif

SELECTED_COMPONENT := $(firstword $(COMMAND_ARGS))
COMPONENT_ROOT := $(COMPONENT_ROOT.$(COMPONENT_KIND))
COMPONENT_DIR := $(if $(COMPONENT_KIND),$(COMPONENT_ROOT)/$(SELECTED_COMPONENT))
COMPONENT_TEST_DIR := $(COMPONENT_DIR)/tests

ifdef COMPONENT_KIND
PY_TARGETS := $(COMPONENT_DIR)
else
PY_TARGETS := $(PY_COMPONENT_ROOTS)
endif

.PHONY: help lint lint-check format format-check openspec-validate check-dagger-version release check-release-tag tests check-python-component check-test-component $(COMPONENT_KINDS) $(COMPONENT_NAMES)

help:
	@printf '%s\n' \
		'Targets:' \
		'  make lint                         Run Ruff lint and fix all Python components without cache' \
		'  make lint module helm             Run Ruff lint and fix one module without cache' \
		'  make lint scenario name           Run Ruff lint and fix one scenario without cache' \
		'  make lint-check                   Check Ruff lint for all Python components without cache' \
		'  make lint-check module helm       Check Ruff lint for one module without cache' \
		'  make lint-check scenario name     Check Ruff lint for one scenario without cache' \
		'  make format                       Format all Python components with Ruff without cache' \
		'  make format module helm           Format one module with Ruff without cache' \
		'  make format scenario name         Format one scenario with Ruff without cache' \
		'  make format-check                 Check Ruff formatting for all Python components without cache' \
		'  make format-check module helm     Check Ruff formatting for one module without cache' \
		'  make format-check scenario name   Check Ruff formatting for one scenario without cache' \
		'  make openspec-validate     Validate OpenSpec specs and changes strictly' \
		'  make check-dagger-version  Check Dagger module and CI versions are aligned' \
		'  make release modules/helm/v0.0.0' \
		'  make release scenarios/name/v0.0.0' \
		'  make tests module helm     Run all Dagger tests for one module' \
		'  make tests scenario name   Run all Dagger tests for one scenario'

check-python-component:
	@if [ -z '$(COMPONENT_KIND)' ] && [ -n '$(SELECTED_COMPONENT)' ]; then \
		printf 'Usage: make $(QUALITY_GOAL) <module|scenario> <name>\n' >&2; \
		exit 2; \
	fi
	@if [ '$(words $(COMPONENT_KIND))' -gt 1 ]; then \
		printf 'Select exactly one component kind: module or scenario\n' >&2; \
		exit 2; \
	fi
	@if [ -n '$(COMPONENT_KIND)' ] && [ -z '$(SELECTED_COMPONENT)' ]; then \
		printf 'Usage: make $(QUALITY_GOAL) <module|scenario> <name>\n' >&2; \
		exit 2; \
	fi
	@if [ -n '$(COMPONENT_KIND)' ] && [ ! -d '$(COMPONENT_DIR)' ]; then \
		printf 'Unknown %s: %s\n' '$(COMPONENT_KIND)' '$(SELECTED_COMPONENT)' >&2; \
		exit 2; \
	fi

lint: check-python-component
	$(RUFF) check --fix $(RUFF_FLAGS) $(PY_TARGETS)

lint-check: check-python-component
	$(RUFF) check $(RUFF_FLAGS) $(PY_TARGETS)

format: check-python-component
	$(RUFF) format $(RUFF_FLAGS) $(PY_TARGETS)

format-check: check-python-component
	$(RUFF) format --check $(RUFF_FLAGS) $(PY_TARGETS)

openspec-validate:
	$(OPENSPEC) validate --all --strict

check-dagger-version:
	python3 scripts/check_dagger_version.py

check-release-tag:
	@if [ -z '$(SELECTED_ARG)' ]; then \
		printf 'Usage: make release modules/<module>/vX.Y.Z\n' >&2; \
		printf '   or: make release scenarios/<scenario>/vX.Y.Z\n' >&2; \
		exit 2; \
	fi
	@branch=$$(git branch --show-current); \
	if [ "$$branch" != master ]; then \
		printf 'Releases must be created from master. Current branch: %s\n' "$$branch" >&2; \
		exit 2; \
	fi
	@case '$(SELECTED_ARG)' in \
		modules/*/v[0-9]*.[0-9]*.[0-9]*) \
			root='$(COMPONENT_ROOT.module)'; \
			kind='module'; \
			;; \
		scenarios/*/v[0-9]*.[0-9]*.[0-9]*) \
			root='$(COMPONENT_ROOT.scenario)'; \
			kind='scenario'; \
			;; \
		*) \
			printf 'Invalid release tag: %s\n' '$(SELECTED_ARG)' >&2; \
			printf 'Usage: make release modules/<module>/vX.Y.Z\n' >&2; \
			printf '   or: make release scenarios/<scenario>/vX.Y.Z\n' >&2; \
			exit 2; \
			;; \
	esac; \
	name=$$(printf '%s\n' '$(SELECTED_ARG)' | cut -d/ -f2); \
	if [ ! -f "$$root/$$name/dagger.json" ]; then \
		printf 'Unknown %s: %s\n' "$$kind" "$$name" >&2; \
		exit 2; \
	fi
	@if git rev-parse -q --verify 'refs/tags/$(SELECTED_ARG)' >/dev/null; then \
		printf 'Release tag already exists: %s\n' '$(SELECTED_ARG)' >&2; \
		exit 2; \
	fi

release: check-release-tag
	git tag -a '$(SELECTED_ARG)' -m 'Release $(SELECTED_ARG)'
	git push origin '$(SELECTED_ARG)'

check-test-component:
	@if [ -z '$(COMPONENT_KIND)' ] || [ -z '$(SELECTED_COMPONENT)' ]; then \
		printf 'Usage: make tests <module|scenario> <name>\n' >&2; \
		exit 2; \
	fi
	@if [ '$(words $(COMPONENT_KIND))' -ne 1 ]; then \
		printf 'Select exactly one component kind: module or scenario\n' >&2; \
		printf 'Usage: make tests <module|scenario> <name>\n' >&2; \
		exit 2; \
	fi
	@if [ ! -d '$(COMPONENT_DIR)' ]; then \
		printf 'Unknown %s: %s\n' '$(COMPONENT_KIND)' '$(SELECTED_COMPONENT)' >&2; \
		exit 2; \
	fi
	@if [ ! -f '$(COMPONENT_TEST_DIR)/dagger.json' ]; then \
		printf '%s has no Dagger test module: %s\n' '$(COMPONENT_KIND)' '$(SELECTED_COMPONENT)' >&2; \
		exit 2; \
	fi

tests: check-test-component
	cd $(COMPONENT_TEST_DIR) && $(DAGGER_ENV) dagger call --progress=plain all

$(COMPONENT_KINDS):
	@:

$(COMPONENT_NAMES):
	@:

$(foreach root,$(COMPONENT_ROOTS),$(root)/%):
	@:
