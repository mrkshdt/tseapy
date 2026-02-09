# Release Checklist

This file defines the minimum "done" state for a public open-source release of `tseapy`.

## Current State

- Packaging metadata exists in `pyproject.toml`
- Wheel/sdist build works locally
- CLI entrypoint (`tseapy`) works
- Docker runtime is defined (`Dockerfile`, `docker-compose.yml`)
- CI validates tests, packaging, and Docker build

## Definition of Done (Public Release)

- [ ] Project version is bumped in `/Users/mrkshdt/Documents/New project/tseapy/tseapy/__init__.py`
- [ ] `README.md` installation and run commands are verified
- [ ] `make test` passes
- [ ] `make build` passes
- [ ] `make wheel-smoke` passes in a network-enabled environment
- [ ] Docker image builds successfully: `docker build -t tseapy:<version> .`
- [ ] Docker runtime starts and serves `/healthz`
- [ ] GitHub Actions CI is green on the release commit
- [ ] Artifacts (`dist/*.whl`, `dist/*.tar.gz`) are published (PyPI or GitHub Release)
- [ ] Release notes are published with major changes and known limitations

## Recommended Release Command Sequence

```bash
make test
make build
make wheel-smoke
docker build -t tseapy:release .
```

Then publish artifacts from `dist/` with your chosen release channel.
