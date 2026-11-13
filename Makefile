# One entry point for the three languages (plan D1). Each target only calls a script under
# tools/ or deploy/scripts/, so a later block adds the script and never edits this file.
# lint, format-check, typecheck and test run tools/quality for Java, TypeScript and Python;
# a missing script fails the target, so no target can pass without running its checks.

S ?=

.PHONY: lint format-check typecheck test suite ci stack-up stack-down

define run_if_present
	@if [ -x "$(1)" ]; then $(1) $(2); else echo "make $@: $(1) does not exist yet, nothing to run"; fi
endef

define run_required
	@if [ -x "$(1)" ]; then $(1) $(2); else echo "make $@: $(1) does not exist yet" >&2; exit 1; fi
endef

lint:
	$(call run_required,tools/lint)

format-check:
	$(call run_required,tools/format-check)

typecheck:
	$(call run_required,tools/typecheck)

test:
	$(call run_required,tools/test)

suite:
	@test -n "$(S)" || { echo "usage: make suite S=<suite id>" >&2; exit 2; }
	$(call run_required,tools/suite,$(S))

ci:
	$(call run_if_present,deploy/scripts/stack-guard.sh)
	@$(MAKE) --no-print-directory lint format-check typecheck test
	$(call run_required,tools/check-suites)

stack-up:
	$(call run_required,deploy/scripts/dev-stack.sh,up)

stack-down:
	$(call run_required,deploy/scripts/dev-stack.sh,down)
