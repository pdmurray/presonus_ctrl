# Publishing Guide

This project is already set up to support CI, local package builds, `pipx`
installation, and GitHub release artifacts. This document captures the current
release flow and the intended future steps for PyPI and AUR publication.

## Current State

Already in place:

- GitHub Actions CI for lint, tests, package build, and CLI smoke tests
- GitHub Actions release workflow for tags matching `v*`
- sdist and wheel generation via `python -m build`
- local `pipx install .` support

Not yet enabled:

- automatic PyPI publication
- AUR packaging/update automation

## Current Release Flow

### 1. Update Version

Update the version in `pyproject.toml`.

### 2. Run Local Verification

From the project root:

```bash
ruff check presonus cli
python3 -m pytest tests/ -q
python3 -m build
```

Optional `pipx` smoke test:

```bash
python3 -m pipx install --force --suffix=-release-test .
presonus-io24-release-test --help
```

### 3. Commit and Tag

Create a version tag that matches the release workflow pattern:

```bash
git tag v0.1.0
git push origin v0.1.0
```

### 4. GitHub Actions Release Job

The release workflow will:

- build sdist and wheel artifacts
- upload them as workflow artifacts
- create a GitHub release
- attach the built artifacts to that release

## Future PyPI Publishing

Recommended approach: trusted publishing from GitHub Actions.

Why:

- avoids long-lived API tokens in repository secrets
- fits well with tag-based releases
- works cleanly with the existing release workflow

### Suggested Future Steps

1. Create the project on PyPI
2. Configure trusted publishing for this GitHub repository
3. Add a `publish-pypi` job triggered from release tags
4. Upload the already-built `dist/*` artifacts to PyPI

When that is ready, the user install flow becomes:

```bash
pipx install presonus-io24
presonus-io24 info
```

## Future AUR Packaging

This project looks like a good future fit for the AUR once the user workflow is
stable.

Likely package forms:

- `presonus-io24` for release tarballs
- possibly `presonus-io24-git` for live VCS packaging

### Suggested Future AUR Plan

1. Wait until release cadence and dependency story are stable
2. Publish tagged GitHub releases consistently
3. Create an AUR `PKGBUILD` that installs the Python package and console script
4. Decide whether to package:
   - only release tarballs
   - only a `-git` package
   - or both

### Notes for AUR Readiness

- Package name and CLI name are already reasonable
- `pyproject.toml` metadata is mostly ready
- The main functional readiness question is protocol maturity, not packaging

## Practical Publishing Checklist

- [ ] Version updated in `pyproject.toml`
- [ ] Lint passes
- [ ] Tests pass
- [ ] Build passes
- [ ] Tag created and pushed
- [ ] GitHub release artifacts created
- [ ] PyPI publication enabled later
- [ ] AUR package added later if desired
