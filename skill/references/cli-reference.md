# Codex CLI reference for `$imagegen`

## Contents

- Verified baseline
- Safe launcher
- Input and output boundaries
- Transparent PNG validation
- Size rules
- Cost and limits
- Troubleshooting

## Verified baseline

Use `codex-cli 0.149.0` or newer. This baseline provides the launcher controls used to ignore local configuration and rules, disable unrelated tool features, select a read-only sandbox, constrain the final response with JSON Schema, and run in an empty temporary working directory.

The `$imagegen` output layout under `$CODEX_HOME/generated_images/` is observed behavior rather than a public compatibility contract. Treat `0.149.0` as the last known-good baseline and rerun the repository tests when upgrading Codex.

## Safe launcher

Write the complete brief, including the literal `$imagegen`, to a UTF-8 file with the host's file-write tool. Never interpolate the prompt into a command string.

```bash
python3 "<SKILL_DIR>/scripts/run_codex_imagegen.py" \
  --prompt-file "<PROMPT_FILE>"
```

Attach reference and edit images in the same order as their role labels:

```bash
python3 "<SKILL_DIR>/scripts/run_codex_imagegen.py" \
  --prompt-file "<PROMPT_FILE>" \
  --image "./base.png" \
  --image "./style-reference.webp"
```

The launcher applies these controls:

- Send the prompt over stdin with a subprocess argument array.
- Run an ephemeral session with `--sandbox read-only`.
- Use `--ignore-user-config` and `--ignore-rules`.
- Disable shell, unified execution, hooks, plugins, apps, browser, computer-use, and multi-agent features.
- Run from a newly created empty temporary directory.
- Pass only an allowlist of runtime environment variables.
- Limit prompt and attachment sizes and verify PNG/JPEG/WebP attachment signatures.
- Require a JSON-schema final response containing only generated PNG paths.
- Accept only existing non-symlink PNGs under `$CODEX_HOME/generated_images/`.

Do not remove a control when generation fails. Report the failure or upgrade the Codex CLI.

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

## Size rules

GPT Image 2 size constraints are deterministic:

- both edges are multiples of 16;
- maximum edge is 3840;
- long:short ratio is at most 3:1;
- total pixels are 655,360-8,294,400;
- dimensions above 2560×1440 are experimental.

A 256×256 request is below the pixel floor. Generate a valid 1024×1024 source and downscale. Common valid sizes include 1024×1024, 1536×1024, 1024×1536, 2048×2048, 2048×1152, 3840×2160, and 2160×3840.

## Cost and limits

- A Codex subscription image turn consumes materially more quota than a text turn. Report any reset time from a usage-limit error.
- This skill never switches to direct API billing and never reads or forwards API credentials.
- Quality, masks, and fidelity are not launcher parameters.
- No seed control is exposed. Iterate with change-X/preserve-Y instead of rerolling blindly.

## Troubleshooting

### Codex CLI missing or too old

Install or upgrade with `npm i -g @openai/codex`, then require version 0.149.0 or newer.

### Authentication required

Ask the user to run `codex login` directly. Never request credentials in chat.

### Launcher rejects the prompt or attachment

Use a readable, non-symlink UTF-8 prompt file containing `$imagegen`. Attach only genuine PNG, JPEG, or WebP files within the size limit.

### Launcher times out

The default is 300 seconds. Retry only when generation was clearly still progressing. Never weaken the sandbox or re-enable disabled tools.

### Launcher rejects the structured result

Codex did not return a schema-valid existing PNG inside the generated-images root. Do not copy another agent-provided path. Rerun once with the same restrictions.

### Transparent output is opaque

Restate genuine alpha, fully transparent corners, no matte, and no checkerboard. Retry once, then run `verify_png_alpha.py` again. Report failure if the second result is still opaque.

### Output is off-style

Fill every schema slot, replace empty adjectives, specify exact text and layout, and iterate with one change while restating all invariants.
