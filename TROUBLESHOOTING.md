# Troubleshooting

## `ModuleNotFoundError: No module named 'tseapy'` when running `tseapy`

Cause:
- broken editable install on some Python 3.13 setups
- stale virtual environment

Fix:

```bash
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip setuptools wheel
python -m pip install .
tseapy --help
```

## `statsmodels is required for STL decomposition`

Cause:
- missing or corrupted `statsmodels` install in current environment

Fix:

```bash
python -m pip install --force-reinstall statsmodels==0.14.4
python -c "import statsmodels, statsmodels.compat; print(statsmodels.__version__)"
```

If reinstall fails repeatedly, rebuild the virtual environment from scratch.

## `BackendUnavailable: Cannot import 'setuptools.build_meta'`

Cause:
- build tooling missing in venv

Fix:

```bash
python -m pip install -U pip setuptools wheel
python -m pip install .
```

## `Permission denied` when deleting `.venv`

Cause:
- files created with different user or protected permissions

Fix:

```bash
sudo chown -R "$USER":staff .venv
chmod -R u+rwX .venv
rm -rf .venv
```

## `No matching distribution found` during install

Cause:
- network/PyPI connectivity issue
- offline environment

Fix:
- verify internet access
- use wheel install from local artifacts if offline:

```bash
python -m build --no-isolation
python3 -m venv /tmp/tseapy-offline
/tmp/tseapy-offline/bin/pip install --no-deps dist/*.whl
```

## Trusted publishing `invalid-publisher`

Cause:
- mismatch between GitHub workflow claims and PyPI/TestPyPI trusted publisher settings

Checklist:
- owner is exactly `mrkshdt`
- repository is exactly `tseapy`
- workflow file matches exactly:
  - `publish-testpypi.yml` for TestPyPI
  - `publish-pypi.yml` for PyPI
- environment matches exactly:
  - `testpypi` for TestPyPI
  - `pypi` for PyPI
- configured on the correct site:
  - TestPyPI config lives on `test.pypi.org`
  - PyPI config lives on `pypi.org`

## `File already exists` on publish

Cause:
- version already published

Fix:
- bump `tseapy/__init__.py` version
- rebuild and republish
