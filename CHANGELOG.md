# Changelog

All notable changes to **loanpy** are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.0.0] - Unreleased

### Added

- `Cluster.liquid` for Hungarian `l.d` / `l.t͡ʃ` clustering (split from `Cluster.glides`).
- `Altign` class with `gaps` and cluster-aware `get_score` for global-alignment pipelines.
- Modular package layout: `cluster`, `align`, `adapt`, `correspondences`, `edit`, `phonotactics`.
- Public API re-exports in `loanpy.__init__` with `__version__`.
- Sphinx documentation and Read the Docs configuration.
- Pytest suite with coverage reporting.
- GitHub Actions workflow for multi-version Python tests.

### Changed

- **Breaking:** `Cluster.glides` no longer clusters consonants after `l`; use `Cluster.liquid` instead.
- **Breaking:** Removed legacy modules (`core`, `scminer`, `scapplier`, bundled `ipa_all.csv`).
- **Breaking:** `get_correspondences` replaced by `get_sound_correspondences` (paired cognate rows, richer output dict).
- Zero third-party runtime dependencies (stdlib only).
- `Uralign` and `Cluster` APIs consolidated from earlier monolithic `core.py`.
- **Breaking:** `uralign` module renamed to `align`; `Cluster.gaps` moved to `Altign.gaps`.

### Migration from 3.x

- Replace `from loanpy import get_correspondences` with `get_sound_correspondences` and adapt to the new return structure (`AbsoluteFrequency`, etc.).
- Replace `scapplier` / `Adrc` usage with `Adapt` + `loanpy.edit` + `loanpy.phonotactics`.
- Update deep links in CLDF README tables from `loanpy/core.py` to the relevant submodule on GitHub.

[4.0.0]: https://github.com/loanwordbank/loanpy/compare/v3.0.0...v4.0.0
