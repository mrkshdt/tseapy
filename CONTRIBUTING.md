# Contributing to tseapy

## Principles

- Keep changes focused and reversible.
- Prefer explicit failure messages over silent handling.
- Keep user workflows (`pip install`, `tseapy`, upload -> analyze) stable.

## Local Setup

```bash
make install
```

This creates `.venv`, upgrades base tooling, and installs `tseapy`.

Editable install:

```bash
make install-editable
```

## Developer Commands

```bash
make test
make build
make wheel-smoke
make wheel-smoke-offline
make run
```

## What to Validate Before PR

- `make test` passes.
- `make build` passes.
- CLI starts (`tseapy --help`).
- Main browser flow works:
  1. upload CSV
  2. configure columns
  3. run at least one algorithm

## Pull Requests

- Use small PRs with a clear objective.
- Include a short validation section in PR description:
  - commands run
  - outcomes
  - limitations (if any)
- If behavior changed, update:
  - `README.md`
  - `TROUBLESHOOTING.md`
  - `CHANGELOG.md` (under `Unreleased`)

## Release-Related Changes

If your PR impacts packaging, publishing, or deployment paths, also update:
- `RELEASE.md`
- `VERSIONING.md`

## Changelog Process

When your PR affects user-visible behavior:

1. Add an entry in `CHANGELOG.md` under `Unreleased`.
2. Use one of: `Added`, `Changed`, `Fixed`, `Removed`.
3. Keep entries concise and outcome-focused.

## Docker Runtime

```bash
docker build -t tseapy:local .
docker run --rm -p 5000:5000 -e TSEAPY_SECRET_KEY=dev-secret tseapy:local
curl http://127.0.0.1:5000/healthz
```
