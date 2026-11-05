# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Docs
- docs: insert real Zenodo DOIs (concept 10.5281/zenodo.20172479, version 10.5281/zenodo.20172480)

### CI
- ci: drop Python 3.10 from matrix (modern scipy/numpy require >=3.11)
- ci: test failures now fail the job; bump checkout and setup-python to v7
- ci: Dependabot no longer raises floors in requirements.txt; action updates are grouped

### Added
- run_all.py runs the documented pipeline in order

### Fixed
- Inverse data described as synthetic galvanic current, not impedance
- Engine log reports the cycles actually run (100), not the configured 500
- Replace deprecated datetime.utcnow()

### Removed
- ruff code-style badge (no ruff config or check exists in this repository)

## [1.0.1] - 2026-05-13

### Changed
- chore(release): prep v1.0.1 — Zenodo metadata, DOI badge, How to Cite
- chore(meta): add CI matrix, Dependabot, and Integrity Code Series cross-links

### Other
- Update README.md

[1.0.1]: https://github.com/felipearocha/integrity-code-series-week6-smartphone-galvanic/releases/tag/v1.0.1
## [1.0.0] - 2026-03-23

### Other
- Initial commit: Week 6 smartphone galvanic corrosion simulation
- Initial commit

[1.0.0]: https://github.com/felipearocha/integrity-code-series-week6-smartphone-galvanic/releases/tag/v1.0.0
