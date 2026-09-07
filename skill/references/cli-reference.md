# Codex CLI reference for `$imagegen`

## Contents

- Verified baseline
- Safe launcher
- Relay model
- Input and output boundaries
- Transparent PNG validation
- Size behavior
- Cost and limits
- Troubleshooting

## Verified baseline

Use `codex-cli 0.149.0` or newer; the launcher and this document were last verified end to end on `codex-cli 0.153.2` (macOS, 2026-09-07). This baseline provides the launcher controls used to ignore local configuration and rules, disable unrelated tool features, select a read-only sandbox, constrain the final response with JSON Schema, pin the relay model, and run in an empty temporary working directory.

The `$imagegen` output layout under `$CODEX_HOME/generated_images/` (currently `<session-id>/exec-<uuid>.png`) is observed behavior rather than a public compatibility contract; the launcher validates paths by root, existence, and type rather than by filename pattern. Treat `0.153.2` as the last known-good baseline and rerun the repository tests when upgrading Codex.

## Safe launcher

Write the complete brief, including the literal `$imagegen`, to a UTF-8 file with the host's file-write tool. Never interpolate the prompt into a command string.

```bash
python3 "<SKILL_DIR>/scripts/run_codex_imagegen.py" \
  --prompt-file "<PROMPT_FILE>" \
  --model gpt-5.6-luna --reasoning-effort none
```

Attach reference and edit images in the same order as their role labels:

```bash
python3 "<SKILL_DIR>/scripts/run_codex_imagegen.py" \
  --prompt-file "<PROMPT_FILE>" \
  --model gpt-5.6-luna --reasoning-effort none \
  --image "./base.png" \
  --image "./style-reference.webp"
```

Options: `--prompt-file` (required), `--image` (repeatable), `--model`, `--reasoning-effort`, `--timeout` (seconds, default 300).

The launcher applies these controls:

- Send the prompt over stdin with a subprocess argument array, terminating the option list with `--` so the variadic `--image` option cannot consume the stdin marker.
- Pass `--model` as `-m` and `--reasoning-effort` as `-c model_reasoning_effort="<level>"`, and retry once with the account default model when Codex rejects the slug.
- Run an ephemeral session with `--sandbox read-only`.
- Use `--ignore-user-config` and `--ignore-rules`.
- Disable shell, unified execution, hooks, plugins, apps, browser, computer-use, and multi-agent features.
- Run from a newly created empty temporary directory.
- Pass only an allowlist of runtime environment variables.
- Limit prompt and attachment sizes and verify PNG/JPEG/WebP attachment signatures.
- Require a JSON-schema final response containing only generated PNG paths.
- Accept only existing non-symlink PNGs under `$CODEX_HOME/generated_images/`.

Do not remove a control when generation fails. Report the failure or upgrade the Codex CLI.

The launcher keeps the child transcript in memory and prints only its own diagnostics: on failure it appends the `error.message` field from Codex's structured `ERROR:` line (for example the usage-limit reset time or an unsupported-model message), never the echoed brief.

## Relay model

In this skill the Codex agent is a relay: the host writes the finished brief, and the agent normalizes it and calls the built-in image tool. Model capability does not change the image, so choose the relay by usage-limit weight.

Codex subscription usage is one shared allowance per plan, drawn down at model-specific rates. OpenAI's pricing page (September 2026) lists Plus local messages per 5-hour window as GPT-6 Astra 5–45 · GPT-5.6 Sol 10–100 · GPT-5.6 Terra 25–200 · GPT-5.6 Luna 250–2,000 · GPT-5.5 15–80 · GPT-5.4 mini 60–350, and notes that image generations use included limits 3–5× faster. Weekly limits also apply.

Measured on 0.153.2 (Plus account, same transparent-star brief):

| Relay | Effort | Reasoning tokens | Turn tokens | Wall time | 5-hour meter delta |
|---|---|---|---|---|---|
| gpt-6-astra (account default) | medium | 0 | 16,029 | ~58 s | about +2% |
| gpt-5.6-luna | none | 0 | 23,370 | 41–53 s | 0–1% |

Turn tokens do not shrink on the light model: most of each turn is fixed context (the built-in imagegen skill text, tool definitions, and the returned image), and reasoning tokens are already zero. The meter is reported in whole percents, so the pricing table is the better guide to the ratio. Image quality was indistinguishable, because the brief is already written in the tool's native schema.

Slug handling:

- Model slugs rotate and are account-specific. The catalog Codex last fetched is in `$CODEX_HOME/models_cache.json`; it refreshes during sessions.
- An unknown slug fails in about six seconds with `400 invalid_request_error: The '<slug>' model is not supported when using Codex with a ChatGPT account` before any image is generated. The launcher detects this, prints `model '<slug>' is not available on this account; retrying with the account default model`, and reruns once without `-m`.
- Effort levels are per model. On 0.153.2, `gpt-5.6-luna` accepts `none`, `low`, `medium`, `high`, `xhigh`, and `max`; `gpt-6-astra` has no `none` and starts at `low`; `minimal` is rejected everywhere. An unsupported effort fails the run with the API message.
- `--model` and `--reasoning-effort` override only this run; `--ignore-user-config` remains in effect.

## Input and output boundaries

The launcher rejects:

- empty prompts, prompts without `$imagegen`, prompts larger than 64 KiB, and symlinked prompt files;
- attachments larger than 50 MiB, symlinks, unsupported extensions, and extension/signature mismatches;
- free-form final messages, extra JSON fields, relative output paths, more than eight paths, duplicate paths, symlinks, missing files, non-PNG files, and paths outside the generated-images root.

Only stdout lines emitted after all checks pass are trusted source PNG paths. The child transcript is suppressed so the image brief is not echoed into host logs, and no diagnostic stream is parsed for paths.

After validation, copy or resize in the host's approved context. On macOS, `sips` uses height before width:

```bash
cp "$SRC" ./output.png
sips -z 256 256 ./output.png
sips -z 900 1600 ./hero-banner.png
sips -z 630 1200 ./og-card.png
```

On Linux, ImageMagick uses width first:

```bash
convert input.png -resize 1600x900! output.png
```

## Transparent PNG validation

GPT Image 2 supports transparent backgrounds in preview. Ask the built-in image-generation tool for genuine transparency and preserve the alpha channel. Include these requirements in the brief:

```text
Background: genuinely transparent with a real alpha channel.
Constraints: fully transparent canvas corners; smooth anti-aliased edge alpha.
Avoid: checkerboard pattern, white or colored matte, floor plane, cast shadow, or reflection.
```

Validate the returned PNG before copying it into the project:

```bash
python3 "<SKILL_DIR>/scripts/verify_png_alpha.py" \
  --require-transparent-corners "$SRC"
```

The validator uses only the Python standard library. It verifies PNG chunk CRCs, decodes non-interlaced 8-bit gray-alpha or RGBA scanlines, requires alpha extrema of 0 and 255, optionally requires four transparent corners, and reports transparent, partial, and opaque pixel counts.

If validation fails, retry once with the full transparent-output brief. Never substitute a painted checkerboard, white background, or unverified post-processing result.

## Size behavior

The built-in image tool exposes no size parameter to the Codex agent. It holds the total area at ≈1.57 megapixels (1254 × 1254 = 1,572,516) and picks the dimensions from the aspect ratio it reads in the brief. Observed on one machine across 393 outputs from codex-cli 0.14x–0.153.2, every file was 1.572–1.574 MP:

| Aspect in brief | Output |
|---|---|
| 1:1 | 1254×1254 |
| 3:2 / 2:3 | 1536×1024 / 1024×1536 |
| 16:9 / 9:16 | 1672×941 / 941×1672 |
| 1.91:1 (OG card) | 1730×909 |
| 2:1 | 1774×887 |
| 3:1 | 2048×768 |

Pixel dimensions in the brief are ignored: "1024×1024" and "256×256" both return 1254×1254. The Images API constraints for gpt-image-2 (edges in multiples of 16, a 655,360-pixel floor, a 3:1 ratio cap) describe the API's `size` parameter, not this path; 1254 is not a multiple of 16.

Therefore write the aspect ratio into `Asset type` ("16:9 landscape hero", "1:1 app icon", "1.91:1 OG card") and produce the exact pixel size by resizing the validated source on the host. Ratios beyond 3:1 have not been observed; crop on the host for extreme banners.

## Cost and limits

- A Codex subscription image turn consumes materially more quota than a text turn, and the shared allowance is drawn down at model-specific rates; run the relay on a light model (see Relay model). Report any reset time from a usage-limit error; the launcher prints it from Codex's structured error line.
- This skill never switches to direct API billing and never reads or forwards API credentials.
- Quality, masks, and fidelity are not launcher parameters.
- No seed control is exposed. Iterate with change-X/preserve-Y instead of rerolling blindly.

## Troubleshooting

### Codex CLI missing or too old

Install or upgrade with `npm i -g @openai/codex`, then require version 0.149.0 or newer (verified on 0.153.2).

### Authentication required

Ask the user to run `codex login` directly. Never request credentials in chat.

### Launcher rejects the prompt or attachment

Use a readable, non-symlink UTF-8 prompt file containing `$imagegen`. Attach only genuine PNG, JPEG, or WebP files within the size limit.

### Launcher times out

The default is 300 seconds. Retry only when generation was clearly still progressing. Never weaken the sandbox or re-enable disabled tools.

### Launcher rejects the structured result

Codex did not return a schema-valid existing PNG inside the generated-images root. Do not copy another agent-provided path. Rerun once with the same restrictions.

### `model '<slug>' is not available on this account; retrying with the account default model`

The `--model` slug is not in the account's catalog. The run already continued on the default model. Update the slug from `$CODEX_HOME/models_cache.json` or omit `--model`.

### Output has the wrong pixel size

Expected: the built-in tool renders ≈1.57 MP at the brief's aspect ratio. Check that the aspect ratio in the brief is right, then resize on the host.

### Transparent output is opaque

Restate genuine alpha, fully transparent corners, no matte, and no checkerboard. Retry once, then run `verify_png_alpha.py` again. Report failure if the second result is still opaque. If the run was an edit of an attached image, this is expected on 0.153.2: edits return opaque PNGs, often with a painted checkerboard. Regenerate the asset from an updated brief instead.

### Output is off-style

Fill every schema slot, replace empty adjectives, specify exact text and layout, and iterate with one change while restating all invariants.
