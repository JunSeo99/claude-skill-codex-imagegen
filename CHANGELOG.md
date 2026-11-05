# Changelog

All notable changes to this project are documented here. The project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-11-05

The first stable release: the brief Claude writes now carries real art direction, the docs match what Codex does after Images 2.6, and the demo shows a full direction-to-set workflow.

### Added

- Art direction section in the prompting guide: value contrast between subject and background, three-color palette roles with one accent, one focal subject, an idea instead of a literal scene, material and light, and clichés to cut. SKILL.md asks Claude to settle these before writing a styled brief.
- Icons and in-app assets section and a consistent-sets section with a reusable style lock, plus official advice on text, photorealism, and reference roles.
- `image_project.py` forwards `--model`, `--reasoning-effort`, `--timeout`, and `--allow-default-model-fallback` to every job, including detached workers. The default and recommended relay stays `gpt-6-luna`.
- Exact-size export example (`sips` resize plus crop) in the CLI reference.

### Changed

- New README demo: three onboarding-illustration directions for a notes app, then four transparent in-app icons and an empty state in the chosen style. Briefs and plans are in `tests/prompts/demo/`. The earlier coffee-cup demo images, briefs, and examples were removed.
- Image model wording updated for Images 2.6 (2026-11-04): Codex picks the image model server-side, and outputs are never labeled with a GPT Image version or variant. API-only 2.6 features (complexity, markup edits, SVG, GIF) are documented as unavailable on this path.
- Transparency guidance: describe only the isolated subject, because a described backdrop can override the transparency flag. Cutouts of existing photos are re-rendered, so compare labels and framing with the source; a 0.166.0 test kept dense label text correct.
- Frontmatter description covers app icons and UI assets and excludes vector, animation, and image-API code requests.
- The transparency test brief uses the skill's own brief format and no longer starts with `$imagegen`.
- READMEs: updated relay-token figures, scripting paths that follow `output/imagegen/<purpose>/`, and synced translations.
- Docs: 2026-11-05 validation run, model research re-check, and SECURITY note that Codex still injects the global `~/.codex/AGENTS.md` into the relay.

## [0.4.0] - 2026-11-02

### Changed

- Default relay is now `gpt-6-luna` (reasoning `none`), verified on codex-cli 0.164.0 and 0.166.0.
- Minimum/verified Codex CLI raised to 0.164.0.
- Briefs no longer need `$imagegen`; the launcher strips it, because the mention made Codex inject its whole imagegen skill into every relay request. With permission and collaboration instructions also disabled, input per relay request fell from about 10,800 to 5,900 tokens.
- Output PNGs are read from `generated_images/<session id>/`, using the session id from Codex's stderr header; model-reported paths are only a fallback.
- Relay instructions set the built-in tool's new `transparent_background` flag when the brief asks for a transparent background.
- Transparency guidance updated: a 0.164.0 cutout returned real RGBA with clear corners; check outline fringes.
- Validation notes record 0.164.0 and 0.166.0 results and much higher, variable relay token counts than the 0.153.4 measurement.
- CI runs on `ubuntu-24.04`; `ubuntu-latest` (26.04) no longer provides Python 3.9.

### Added

- `.claude-plugin/plugin.json` and `marketplace.json`: install as a Claude Code plugin; `npx skills add` keeps working.
- `skill/scripts/codex_status.py`: Codex version, login, and relay-model check without a model call.
- `skill/scripts/solidify_png_alpha.py`: writes a copy with near-opaque alpha raised to 255 (subjects come back at alpha 250–254).
- SKILL.md asks Claude to keep the final brief as `output/imagegen/<purpose>/<image-name>.md`, never inside the user's (possibly served) export destination.

### Fixed

- On codex-cli 0.164.0 the relay calls the image tool through the code-mode `exec` wrapper and often never sees the saved path, so it returned empty or invented paths and the launcher refused every generation although the image had been saved.

## [0.3.0] - 2026-09-10

### Added

- Intent-aware workflows for optional creative interviews, distinct directions, reference edits, consistent sets, and visual review.
- Subscription-only background image jobs: detached workers, immediate job handles, local status, bounded parallel generation (default 2, maximum 4).
- Separate PNGs, comparison galleries, checkpoint manifests, and verified resume that skips completed images.
- GPT Image 2.5 research distinguishing Flare/Sunburst strengths from the image controls actually exposed by Codex.
- Live generation/edit examples, public prompts, context measurements, and tests for background dispatch, concurrent work, failure handling, and resume.

### Changed

- Default to `gpt-5.6-luna` with reasoning `none`; automatic fallback to a heavier account-default relay now requires `--allow-default-model-fallback`.
- Replace generic coding instructions with a compact image relay; omit the skills catalog and disable unrelated capabilities.
- Reduce the skill entrypoint from 2,198 to 762 whitespace-delimited words and load conditional references only when needed.
- Require Codex CLI 0.153.4+ for the verified context controls.
- Rebuild English, Korean, Japanese, and Chinese READMEs around real outputs and copyable workflows.
- Move demonstration assets outside the installed skill, reducing the distributable to roughly 22 KB.
- Treat older size/transparent-edit results as dated observations; inspect current output rather than declaring permanent model limitations.

### Boundaries

- No separate image API route, API credential handling, or automatic billing change.
- `--model` is the Codex text relay. The subscription image backend remains Codex-managed; Flare/Sunburst cannot currently be pinned through this launcher.

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
