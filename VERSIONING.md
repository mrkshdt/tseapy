# Versioning Policy

`tseapy` uses semantic versioning with optional pre-release suffixes:

- stable: `MAJOR.MINOR.PATCH` (example: `1.2.0`)
- pre-release: `MAJOR.MINOR.PATCHaN`, `bN`, or `rcN` (example: `1.2.0a0`)

## Bump Rules

- `PATCH`: bug fix, no intended behavior break
- `MINOR`: new features, backwards-compatible
- `MAJOR`: breaking changes in behavior or interfaces

## Pre-Release Rules

- Use `a` for early validation and packaging tests
- Use `b` for feature-complete testing
- Use `rc` for release candidate
- Final release drops suffix (for example `1.2.0rc1` -> `1.2.0`)

## Where to Update Version

Single source of truth:
- `tseapy/__init__.py`

## Release Hygiene

Before publishing:
- update `CHANGELOG.md` for the target version
- ensure version is not already published
- run release checks in `RELEASE.md`
