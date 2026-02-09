PYTHON ?= python3
VENV ?= .venv
WHEEL_TEST_VENV ?= /tmp/tseapy-wheel-test

PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
PYTHON_VENV := $(VENV)/bin/python
TSEAPY := $(VENV)/bin/tseapy

.PHONY: venv install install-editable test run build wheel-smoke wheel-smoke-offline clean-build

venv:
	$(PYTHON) -m venv $(VENV)

install: venv
	$(PIP) install --upgrade pip
	$(PIP) install setuptools wheel
	$(PIP) install --no-build-isolation .

install-editable: venv
	$(PIP) install --upgrade pip
	$(PIP) install setuptools wheel
	$(PIP) install --no-build-isolation -e .

test:
	$(PYTEST) -q

run:
	$(TSEAPY) --host 127.0.0.1 --port 5000 --no-debug

clean-build:
	rm -rf dist build *.egg-info

build: clean-build
	$(PYTHON_VENV) -m build --no-isolation

wheel-smoke: build
	rm -rf $(WHEEL_TEST_VENV)
	$(PYTHON) -m venv $(WHEEL_TEST_VENV)
	$(WHEEL_TEST_VENV)/bin/pip install --upgrade pip
	$(WHEEL_TEST_VENV)/bin/pip install dist/*.whl
	$(WHEEL_TEST_VENV)/bin/tseapy --help

wheel-smoke-offline: build
	rm -rf $(WHEEL_TEST_VENV)
	$(PYTHON) -m venv $(WHEEL_TEST_VENV)
	$(WHEEL_TEST_VENV)/bin/pip install --no-deps dist/*.whl
	$(WHEEL_TEST_VENV)/bin/tseapy --help
