# Release Runbook

This document defines the release process for publishing `tseapy` to TestPyPI and PyPI.

## Definition of Done

- [ ] Version bumped in `tseapy/__init__.py`
- [ ] `CHANGELOG.md` updated
- [ ] `README.md` and `TROUBLESHOOTING.md` reflect current behavior
- [ ] `make test` passes
- [ ] `make build` passes
- [ ] `make wheel-smoke` passes in networked environment
- [ ] TestPyPI publish succeeds
- [ ] Install test from TestPyPI succeeds in a clean venv
- [ ] PyPI publish succeeds
- [ ] Install test from PyPI succeeds in a clean venv

## Pre-Release Validation

```bash
make test
make build
make wheel-smoke
docker build -t tseapy:release .
```

## Trusted Publishing (OIDC)

Expected trusted publisher values:

- Owner: `mrkshdt`
- Repository: `tseapy`
- TestPyPI workflow file: `publish-testpypi.yml`
- TestPyPI environment: `testpypi`
- PyPI workflow file: `publish-pypi.yml`
- PyPI environment: `pypi`

Workflow files:
- `.github/workflows/publish-testpypi.yml`
- `.github/workflows/publish-pypi.yml`

## Publish to TestPyPI

1. Ensure version is new (never uploaded before).
2. Run GitHub Action `Publish TestPyPI` (manual dispatch).
3. Verify install:

```bash
python3 -m venv /tmp/tseapy-testpypi
/tmp/tseapy-testpypi/bin/pip install -U pip
/tmp/tseapy-testpypi/bin/pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple \
  "tseapy==<version>"
/tmp/tseapy-testpypi/bin/tseapy --help
```

## Publish to PyPI

Two options:
- publish a GitHub Release (triggers `Publish PyPI`)
- run `Publish PyPI` manually

Verify install:

```bash
python3 -m venv /tmp/tseapy-pypi
/tmp/tseapy-pypi/bin/pip install -U pip
/tmp/tseapy-pypi/bin/pip install "tseapy==<version>"
/tmp/tseapy-pypi/bin/tseapy --help
```

## Common Release Failures

- `invalid-publisher`:
  - publisher exists on wrong site (`test.pypi.org` vs `pypi.org`)
  - owner/repo/workflow/environment mismatch
- `file already exists`:
  - version already published; bump version and republish
- dependency resolution failures:
  - verify lockstep between `pyproject.toml` and tested environment
