# Changelog

All notable changes to this project are documented here. The project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.3] - 2026-09-07

### Added

- `run_codex_imagegen.py`: optional `--model` and `--reasoning-effort` relay-model controls (`-m` / `-c model_reasoning_effort`), with one automatic retry on the account default model when Codex rejects the slug; the skill runs the relay on the lightest listed model because Codex usage limits are shared and drawn down at model-specific rates.
- Documented the measured relay-model comparison on codex-cli 0.153.2 (tokens unchanged, 5-hour meter about 2% per image on GPT-6 Astra versus 0–1% on GPT-5.6 Luna, identical image quality).
- Failure diagnostics: the launcher now reports the `error.message` field from Codex's structured `ERROR:` line (usage-limit reset time, unsupported model or effort) while still suppressing the transcript.

### Changed

- Corrected size guidance: the built-in image tool has no size parameter and renders ≈1.57 megapixels at the aspect ratio read from the brief (393 outputs observed); briefs state the aspect ratio and the host resizes. The Images API `size` constraints no longer appear as built-in behavior.
- Raised the verified Codex CLI baseline to 0.153.2 (minimum remains 0.149.0); re-verified native transparent output through the launcher with the light relay model.
- Documented that built-in edits of transparent images return opaque PNGs; regenerate instead of editing.
- Terminated the `codex exec` option list with `--` so the variadic `--image` option cannot consume the stdin prompt marker.
- Removed remaining references to CLI-only `--quality` and `--mask` controls that this skill does not expose.

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
