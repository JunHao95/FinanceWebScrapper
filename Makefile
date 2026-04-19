.PHONY: test test-unit test-integration test-regression test-e2e

test: test-unit test-integration test-regression test-e2e

test-unit:
	pytest -m unit -q

test-integration:
	pytest -m integration -q

test-regression:
	pytest -m regression -q

test-e2e:
	pytest -m e2e -q --browser chromium
