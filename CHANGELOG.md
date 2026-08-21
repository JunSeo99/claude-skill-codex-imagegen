# Changelog

All notable changes to this project are documented here. The project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.2] - 2026-08-21

### Added

- `skill/scripts/verify_png_alpha.py`: dependency-free decoded-pixel verification for RGBA/gray-alpha PNGs, including alpha extrema, transparent corners, and pixel counts.
- GitHub Actions CI and standard-library unit tests for the launcher security boundary, alpha validator, documentation claims, and packaged `.skill` parity.
- Live transparent-output validation against `codex-cli 0.149.0`: RGBA output with alpha extrema 0–255 and all four corners fully transparent.

### Changed

- Corrected the obsolete transparency description: GPT Image 2 supports transparent backgrounds in preview.
- Replaced obsolete workaround and alternate-model guidance with native-alpha prompting plus decoded-pixel validation.
- Reduced the distributed skill to one Codex subscription path; it does not switch to direct API billing or read API credentials.
- Raised the supported Codex CLI baseline to 0.149.0.

### Security

- Run Codex from an empty temporary directory with user config and project rules ignored.
- Disable shell, unified execution, hooks, plugins, apps, browser, computer-use, and multi-agent features.
- Allowlist the subprocess environment, validate attachment signatures and sizes, and require a JSON-schema final response.
- Parse only the structured final message and accept only existing non-symlink PNGs inside the generated-images root.

## [0.2.1] - 2026-08-21

### Added

- `skill/scripts/run_codex_imagegen.py`: prompt-file/stdin transport, ephemeral read-only Codex execution, and generated-path validation.

### Changed

- Updated all quickstarts to use `npx skills add ... --skill codex-imagegen` so successful installs can participate in anonymous skills.sh telemetry.
- Rewrote security documentation around prompt transport, path validation, and sandboxing.
- Updated English, Korean, Japanese, and Simplified Chinese installation instructions.

### Removed

- The opt-in unsandboxed execution path and direct prompt interpolation examples.

## [0.2.0] - 2026-07-10

### Added

- Native-schema prompting, multiple reference-image role labeling, character-consistency guidance, deterministic size rules, and transparent-asset experiments.
- Expanded prompting and CLI references plus additional failure-mode guidance.

### Changed

- Corrected size guidance to the deterministic GPT Image 2 constraints.
- Documented that quality, masks, and fidelity are not Codex subscription launcher parameters.

## [0.1.0] - 2026-05-11

### Added

- Initial Claude Code skill, prompting guide, CLI reference, sample asset, distributable bundle, README, license, and security policy.
