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
- Results and Limitations sections in the README

### Changed
- Corrosion results are labelled as uncalibrated; the port lifetime, economic exposure and multi-scale coupling claims are withdrawn
- Electrolyte potential under 5 V bias is now 0.96 to 3.35 V, and peak current density 1.20e4 A/m2
- GIF labelled illustrative

### Fixed
- Potential-field colorbar said "V vs SHE"; phi is measured from the solver ground (0 V everywhere at zero bias), now labelled "V vs solver ground"
- Laplace boundary update: sign error caused divergence to 1e208 V with converged=True
- Insulators apply the zero-flux condition instead of a fixed potential
- MCMC keeps out-of-prior rejections in the chain (2000 steps, not 1890)
- Inverse data described as synthetic galvanic current, not impedance
- Engine log reports the cycles actually run (100), not the configured 500
- Replace deprecated datetime.utcnow()

### Removed
- ruff code-style badge (no ruff config or check exists in this repository)
- Unverified Apple reference from .zenodo.json

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
