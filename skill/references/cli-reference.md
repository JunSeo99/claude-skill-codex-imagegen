# Codex CLI reference for `$imagegen`

## Contents

- Verified baseline
- Execution paths
- Safe launcher
- Output handling
- Size rules
- Host-run Image API CLI
- Chroma-key helper
- Cost and limits
- Troubleshooting

## Verified baseline

The image workflow was validated against `codex-cli 0.144.1` on macOS, with the safe launcher's stdin and sandbox flags rechecked against 0.147.0. The `$imagegen` output layout, bundled helpers, and invocation semantics are not a public compatibility contract. Treat these versions as last-known-good baselines.

## Execution paths

| | Sandboxed Codex subscription path | Host-run bundled Image API CLI |
|---|---|---|
| What runs | `run_codex_imagegen.py` starts a Codex agent for generation only | Host runs `image_gen.py` directly |
| Auth | Codex login and subscription | Existing `OPENAI_API_KEY`, per-image billing |
| Shell sandbox | Read-only and ephemeral | Host's approved tool context |
| Sensitive environment | API keys, tokens, secrets, passwords, and credentials removed | Host controls the explicit API environment |
| Prompt transport | UTF-8 file → subprocess stdin; no shell interpolation | `--prompt-file` or JSONL input |
| Output trust | Existing PNG must resolve under `$CODEX_HOME/generated_images/` | Explicit host-controlled output path |
| Per-call controls | Image tool defaults | `--size`, `--quality`, `--background`, `--mask`, `--n`, and more |

Use the sandboxed Codex path by default. Use the host-run CLI only when the user already has API billing configured and needs controls not exposed by the Codex image tool.

## Safe launcher

Write the complete brief, including the literal `$imagegen`, to a UTF-8 file with the host's file-write tool. Do not interpolate untrusted prompt text into a shell command.

```bash
python3 "<SKILL_DIR>/scripts/run_codex_imagegen.py" \
  --prompt-file "<PROMPT_FILE>"
```

Reference and edit images are repeatable. Their order must match the role labels in the prompt:

```bash
python3 "<SKILL_DIR>/scripts/run_codex_imagegen.py" \
  --prompt-file "<PROMPT_FILE>" \
  --image "./base.png" \
  --image "./style-reference.png"
```

The launcher uses these Codex controls internally:

- `-` reads the prompt from stdin.
- `--sandbox read-only` prevents model-generated shell writes.
- `--ephemeral` avoids persisting the agent session.
- `--output-last-message` provides a stable final-response source for validation.
- `--skip-git-repo-check` permits generation outside a Git repository.

The launcher appends a fixed instruction to use only the built-in image-generation tool, avoid shell commands and workspace changes, and return absolute PNG paths. It invokes Codex with a subprocess argument list and `shell=False` semantics.

Before starting Codex, the launcher removes environment variables whose names contain `API_KEY`, `TOKEN`, `SECRET`, `PASSWORD`, or `CREDENTIAL`. The subscription path authenticates through the existing Codex login instead.

## Output handling

The generated PNG normally lands at `$CODEX_HOME/generated_images/<session-id>/ig_<hash>.png`, defaulting to `~/.codex/generated_images/...`.

The launcher resolves every returned path canonically and prints it only when all checks pass:

- inside the configured generated-images root after symlink resolution;
- existing regular file;
- `.png` suffix;
- not duplicated in the output.

Do not fall back to copying an arbitrary path printed by the agent. If validation fails, inspect stderr and rerun once.

After validation, the host may copy and resize. `sips` uses height before width:

```bash
cp "$SRC" ./output.png
sips -z 256 256 ./icon.png
sips -z 900 1600 ./hero-banner.png
sips -z 630 1200 ./og-card.png
```

Linux ImageMagick uses width first, and `!` forces exact dimensions:

```bash
convert input.png -resize 1600x900! output.png
```

## Size rules

gpt-image-2 size constraints are deterministic:

- both edges are multiples of 16;
- maximum edge is 3840;
- long:short ratio is at most 3:1;
- total pixels are 655,360-8,294,400;
- dimensions above 2560×1440 are experimental.

A 256×256 request is below the pixel floor. Generate a valid 1024×1024 source and downscale. Common valid sizes include 1024×1024, 1536×1024, 1024×1536, 2048×2048, 2048×1152, 3840×2160, and 2160×3840.

## Host-run bundled Image API CLI

Codex ships `image_gen.py` in its system image-generation skill. The host can run it directly when `OPENAI_API_KEY` is already configured:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/imagegen/scripts/image_gen.py" \
  generate --prompt-file "<PROMPT_FILE>" --out ./output.png
```

Subcommands are `generate`, `edit`, and `generate-batch`. Defaults are model `gpt-image-2`, size `auto`, quality `medium`, and PNG output. `--dry-run` prints the API payload without a network request.

Key flags:

- `--quality low|medium|high|auto`
- `--size WxH`
- `--background transparent` for gpt-image-1.5 only, with PNG or WebP
- `--input-fidelity low|high` for eligible edit models; not gpt-image-2
- `--mask <png>` for the first edit image; same size and alpha required
- repeatable `--image` for multi-image edits
- `--n` for variants of one prompt
- `--no-augment` to send the prompt verbatim
- `--prompt-file`, `--output-compression`, `--moderation`, `--max-attempts`, `--fail-fast`, `--force`, `--downscale-max-dim`, and `--out-dir`

Batch example:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/imagegen/scripts/image_gen.py" \
  generate-batch --input prompts.jsonl --out-dir ./out --concurrency 5
```

JSONL uses one job per line. Each job may override `prompt`, `size`, `quality`, `background`, `output_format`, `n`, `model`, and `out`.

## Chroma-key helper

Codex also ships `remove_chroma_key.py`. Run it on a flat-key generation:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/imagegen/scripts/remove_chroma_key.py" \
  --input "$SRC" --out ./asset.png \
  --auto-key border --soft-matte \
  --transparent-threshold 12 --opaque-threshold 220 --despill
```

Useful flags include `--key-color`, `--tolerance`, `--auto-key none|corners|border`, `--soft-matte`, `--transparent-threshold`, `--opaque-threshold`, `--edge-feather`, `--edge-contract`, `--despill`, and `--force`.

Validate RGBA mode, alpha extrema containing 0 and 255, transparent corners, and no key-color fringe. Try `--edge-contract 1` for a thin fringe. Hard tolerance-only removal is appropriate only for flat pixel art.

## Cost and limits

- A Codex subscription image turn consumes materially more quota than a text turn. Report any reset time from a usage-limit error.
- The host-run CLI uses per-image API billing. Confirm the user wants this path before switching when they did not already request it.
- gpt-image-2 has no native transparent background. Use chroma-key removal or gpt-image-1.5 native alpha.
- Quality, masks, and fidelity controls are not available through the Codex subscription image tool.
- No seed control is exposed. Iterate with change-X/preserve-Y rather than rerolling blindly.

## Troubleshooting

### Codex CLI missing

Install with `npm i -g @openai/codex`.

### Authentication required

Ask the user to run `codex login` directly.

### Launcher rejects the prompt

Use a readable, non-empty UTF-8 file containing the literal `$imagegen`.

### Launcher times out

The default is 300 seconds. Retry only when the generation was clearly still progressing; never weaken the sandbox. An explicit `--timeout` value may increase the bound.

### Launcher rejects the result path

Codex did not return an existing PNG inside the configured generated-images root. Do not copy a different agent-provided path. Inspect stderr and rerun once.

### Output is off-style

Fill every schema slot, replace empty adjectives, specify exact text and layout, and iterate with one change while restating all invariants.

### Transparent output is opaque

Run the chroma-key removal helper and verify alpha. If the subject has complex semi-transparent edges, use the host-run gpt-image-1.5 native-alpha path.
