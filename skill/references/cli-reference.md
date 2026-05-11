# Codex CLI reference for $imagegen

## Verified version

This skill was validated against `codex-cli 0.130.0` (`codex --version`). Internals of the `$imagegen` skill — including the exact output path layout under `~/.codex/generated_images/` — are not part of the Codex CLI's public contract and may change in future versions. Always treat the version stamp here as the last known-good baseline, not a permanent guarantee.

## Two run modes

### Mode A — Safe default

```bash
codex exec [FLAGS] '$imagegen <PROMPT>.
Generate the image and then print ONLY the absolute path of the
resulting PNG on the final line of your reply. Do NOT copy, move,
or modify the file.'
```

The sub-agent is instructed to run only the image-generation tool (no `cp`/`sips`). With `--sandbox workspace-write` plus active approvals, Codex's sandbox blocks writes outside the current workspace and gates elevated operations behind approval prompts — which, run non-interactively, fail rather than execute silently. Writes inside the workspace remain technically possible; we rely on the prompt instruction "do not copy or move" plus the sandbox + approvals to keep blast radius small. The host (Claude Code) parses the absolute path from stdout and performs the file move/resize itself.

### Mode B — Automated (opt-in, requires trust)

```bash
codex exec [FLAGS] --dangerously-bypass-approvals-and-sandbox \
  '$imagegen <PROMPT>. Save to <PATH> at exactly WxH pixels.'
```

`--dangerously-bypass-approvals-and-sandbox` removes Codex's built-in approval prompts AND its execution sandbox. The model can run arbitrary shell commands in your working directory. Only use this in trusted prompts inside trusted repos. See `SECURITY.md` in the repo for the full threat model.

## Required flags (both modes)

- `--sandbox workspace-write` — allow writes inside the current working directory
- `--skip-git-repo-check` — also work outside git repos

## Optional flags

- `-i <file>` — attach a reference / source image (repeatable)
- `-m <model>` — override the agent model (not the image model — leave default)
- `--ephemeral` — do not persist the session

## Output path

As of codex-cli 0.130.0, the raw PNG lands at:

```
$CODEX_HOME/generated_images/<session-uuid>/ig_<hash>.png
# default: ~/.codex/generated_images/...
```

Verified example:
```
~/.codex/generated_images/019e1515-cc8b-7bd3-8d16-7e5e088035dd/ig_0be263cbee14ac3c016a014d4ff52881918cde007093977dbb.png
```

In **Mode A**, you ask the sub-agent to `print` the absolute path; the host parses stdout. Deterministic fallback when parsing fails:

```bash
find ~/.codex/generated_images -name 'ig_*.png' -mmin -3 -type f -print0 \
  | xargs -0 ls -t | head -1
```

In **Mode B**, the sub-agent runs `find` + `cp` itself and the path appears in the final answer.

## Size post-processing

gpt-image-2 does not honor the exact size requested. Verified:
- requested: 256×256
- delivered: 1254×1254

Resize with `sips` on macOS — note arg order is `height width` (not width height):

```bash
sips -z 256 256 ./icon.png            # 256x256 square (order ambiguous when square)
sips -z 900 1600 ./hero-banner.png    # 1600x900 landscape — HEIGHT 900, WIDTH 1600
sips -z 1536 1024 ./og.png            # 1024x1536 portrait  — HEIGHT 1536, WIDTH 1024
sips -z 630 1200 ./og-card.png        # 1200x630 OG card    — HEIGHT 630,  WIDTH 1200
```

On Linux, fall back to ImageMagick (note: `WxH` order — width first):

```bash
convert input.png -resize 1600x900! output.png   # the ! forces exact dimensions
```

## Cost / usage

- **ChatGPT/Codex subscription**: 1 image turn ≈ 3–5 text turns of usage limit
- **API key mode** (`export OPENAI_API_KEY=sk-...`): priced per image
  - Image output: **$30.00 / 1M output tokens**
  - Image input: **$8.00 / 1M input tokens** ($2.00 / 1M cached input)
  - Plus text-input tokens for your prompt (check the [OpenAI pricing page](https://openai.com/api/pricing/) for current text-input rates on this model)
  - Typical per-image cost: roughly $0.04 – $0.35 depending on quality/size

For batches of 10+ images, API-key mode is generally cheaper than the subscription.

## Supported sizes (gpt-image-2)

Per the [OpenAI image-generation guide](https://developers.openai.com/api/docs/guides/image-generation):

- Maximum edge length: **≤ 3840 px**
- Both edges must be **multiples of 16 px**
- Long-edge to short-edge ratio: **≤ 3:1**
- Total pixels: **≥ 655,360** AND **≤ 8,294,400**
- Or pass `size: "auto"` and let the model pick

Common popular sizes the guide mentions: `1024×1024`, `1536×1024`, `1024×1536`, `2048×2048`, `3840×2160`.

Quality enum: `low` / `medium` / `high` / `auto` (default).

## Limits

| Limit | Workaround |
|---|---|
| Transparent PNG not supported on gpt-image-2 | Per [OpenAI guide](https://developers.openai.com/api/docs/guides/image-generation): `Requests with background: "transparent" aren't supported for this model.` Use gpt-image-1.5 via Image API, or post-process |
| Imprecise output size | Add "at exactly WxH pixels" to prompt; host resizes with `sips` |
| Hard to place elements precisely in complex layouts | Simplify, or compose in SVG and convert to PNG |
| Small non-Latin text (CJK, Arabic, etc.) can break | Use larger text + EXACT TEXT marker + double quotes |
| Latency up to 2 min | Set Bash tool timeout ≥ 300000 ms |

## Troubleshooting

### `codex: command not found`
```bash
npm i -g @openai/codex
# Then ask the user to run `! codex login` and retry
```

### Authentication required
Tell the user:
> Run `! codex login` directly in this Claude Code session.

### Output is wildly off
1. Rewrite Subject + Details slots
2. Confirm all five slots are filled
3. Strip empty adjectives ("stunning, cinematic")
4. For text work: EXACT TEXT marker + double quotes + "no duplicate text"

### No file at the expected output path (Mode B) or no path printed (Mode A)
Use the deterministic fallback:
```bash
find ~/.codex/generated_images -name 'ig_*.png' -mmin -3 -type f -print0 \
  | xargs -0 ls -t | head -1
```
The newest-by-mtime is the one just produced.

### Same prompt, different result
Expected. gpt-image-2 is non-deterministic. If/when codex exposes a `seed` option, use it; v0.130 does not.

### Codex CLI was upgraded and `$imagegen` behaves differently
Check `codex --version`. If above 0.130.x, scan the codex changelog for `$imagegen`/`imagegen`/`generated_images` mentions. Output paths and flag semantics are not part of the public contract. Open an issue on this skill's repo with the new behavior so the docs can be updated.
