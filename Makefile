SHELL := /bin/sh

MODULES_DIR := modules
MODULE_NAMES := $(notdir $(wildcard $(MODULES_DIR)/*))
COMMAND_TARGETS := help lint format format-check openspec-validate tests check-module check-test-module
MODULE_ARG := $(filter-out $(COMMAND_TARGETS),$(MAKECMDGOALS))

RUFF ?= ruff
RUFF_FLAGS ?= --no-cache
OPENSPEC ?= openspec
DAGGER_ENV ?= DAGGER_NO_NAG=1 DO_NOT_TRACK=1 DAGGER_NO_UPDATE_CHECK=1

ifneq ($(strip $(MODULE_ARG)),)
SELECTED_MODULE := $(firstword $(MODULE_ARG))
endif

ifdef SELECTED_MODULE
PY_TARGET := $(MODULES_DIR)/$(SELECTED_MODULE)
TEST_TARGET := $(MODULES_DIR)/$(SELECTED_MODULE)/tests
else
PY_TARGET := $(MODULES_DIR)
endif

.PHONY: help lint format format-check openspec-validate tests check-module check-test-module $(MODULE_NAMES)

help:
	@printf '%s\n' \
		'Targets:' \
		'  make lint                  Run Ruff lint for all modules without cache' \
		'  make lint helm             Run Ruff lint for one module without cache' \
		'  make format                Format all modules with Ruff without cache' \
		'  make format helm           Format one module with Ruff without cache' \
		'  make format-check          Check Ruff formatting for all modules without cache' \
		'  make format-check helm     Check Ruff formatting for one module without cache' \
		'  make openspec-validate     Validate OpenSpec specs and changes strictly' \
		'  make tests helm            Run all Dagger tests for one module'

check-module:
	@if [ -n '$(SELECTED_MODULE)' ] && [ ! -d '$(PY_TARGET)' ]; then \
		printf 'Unknown module: %s\n' '$(SELECTED_MODULE)' >&2; \
		exit 2; \
	fi

lint: check-module
	$(RUFF) check $(RUFF_FLAGS) $(PY_TARGET)

format: check-module
	$(RUFF) format $(RUFF_FLAGS) $(PY_TARGET)

format-check: check-module
	$(RUFF) format --check $(RUFF_FLAGS) $(PY_TARGET)

openspec-validate:
	$(OPENSPEC) validate --all --strict

check-test-module:
	@if [ -z '$(SELECTED_MODULE)' ]; then \
		printf 'Usage: make tests <module>\n' >&2; \
		exit 2; \
	fi
	@if [ ! -d '$(PY_TARGET)' ]; then \
		printf 'Unknown module: %s\n' '$(SELECTED_MODULE)' >&2; \
		exit 2; \
	fi
	@if [ ! -f '$(TEST_TARGET)/dagger.json' ]; then \
		printf 'Module has no Dagger test module: %s\n' '$(SELECTED_MODULE)' >&2; \
		exit 2; \
	fi

tests: check-test-module
	cd $(TEST_TARGET) && $(DAGGER_ENV) dagger call --progress=plain all

$(MODULE_NAMES):
	@:
