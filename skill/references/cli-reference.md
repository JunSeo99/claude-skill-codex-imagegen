# Codex CLI reference for $imagegen

## Verified version

Validated against `codex-cli 0.144.1` on macOS (original verification runs: 0.130.0). Internals of the `$imagegen` skill — the output path layout under `~/.codex/generated_images/`, the bundled helper scripts, invocation semantics — are not part of the Codex CLI's public contract and may change. Treat the version stamp as the last known-good baseline, not a guarantee.

## Three execution paths

| | Mode A (default) | Mode B (opt-in) | Host-run bundled CLI |
|---|---|---|---|
| What runs | codex agent, generation only | codex agent, generation + its own post-processing | this host runs `image_gen.py` directly — no codex agent turn |
| Auth | Codex login (subscription) | Codex login (subscription) | `OPENAI_API_KEY` (per-image API billing) |
| Sandbox | active, approvals active | `--dangerously-bypass-approvals-and-sandbox` | n/a (host's own tool context) |
| Prompt handling | agent rewrites into its labeled schema | same | `--no-augment` sends your prompt verbatim |
| Per-call controls | none | none | `--size --quality --background --output-format --mask --n` etc. |

Mode B is a trust hand-off — see `SECURITY.md`. The host-run CLI is both the safest and the most controllable path, but bills per image and needs the `openai` Python package.

## Invocation (Mode A / Mode B)

```bash
# Mode A — safe default: codex generates, host post-processes
codex exec --skip-git-repo-check --sandbox workspace-write \
  '$imagegen <PROMPT>.
Generate the image and then print ONLY the absolute path of the
resulting PNG on the final line of your reply. Do NOT copy, move,
or modify the file.' < /dev/null

# Mode B — opt-in automated: codex also does cp/resize itself
codex exec --skip-git-repo-check --sandbox workspace-write \
  --dangerously-bypass-approvals-and-sandbox \
  '$imagegen <PROMPT>. Save to <PATH> at exactly WxH pixels and print the absolute path.' < /dev/null
```

In Mode A the sub-agent runs only the image-generation tool; the sandbox blocks writes outside the workspace and approval-gated operations fail rather than execute silently when run non-interactively. The host performs the file move/resize itself.

- `< /dev/null` — **required from automation**; codex exec reads stdin alongside the prompt argument and hangs on "Reading additional input from stdin..." otherwise
- `-i <file>` — attach reference/source image (repeatable, order meaningful; label each by index and role in the prompt)
- `-m <model>` — overrides the *agent* model, not the image model; leave default
- `--ephemeral` — do not persist the session
- Bash tool timeout ≥ 300000 ms; complex prompts take up to 2 min

## Output path and host post-processing

The raw PNG lands at `$CODEX_HOME/generated_images/<session-uuid>/ig_<hash>.png` (default `~/.codex/...`). In Mode A, parse the printed path from stdout; deterministic fallback:

```bash
find ~/.codex/generated_images -name 'ig_*.png' -mmin -3 -type f -print0 | xargs -0 ls -t | head -1
```

Then the host finishes locally. `sips` arg order is **height width**:

```bash
cp "$SRC" ./output.png
sips -z 256 256 ./icon.png            # 256x256 square
sips -z 900 1600 ./hero-banner.png    # 1600x900 landscape — HEIGHT 900, WIDTH 1600
sips -z 630 1200 ./og-card.png        # 1200x630 OG card    — HEIGHT 630,  WIDTH 1200
```

Linux (ImageMagick, width-first, `!` forces exact):

```bash
convert input.png -resize 1600x900! output.png
```

## Size: the real rules

gpt-image-2 size constraints are deterministic, not "loose adherence":

- both edges multiples of 16 · max edge ≤ 3840 · long:short ratio ≤ 3:1
- **total pixels 655,360–8,294,400** · above 2560×1440 experimental · or `size: "auto"`

A 256×256 request (65,536 px) violates the pixel floor → the model generates large (verified: 1254×1254). Fix: generate valid (1024×1024) and downscale on the host. In the host-run CLI, `--size WxH` is honored when valid. Popular valid sizes: 1024×1024, 1536×1024, 1024×1536, 2048×2048, 2048×1152, 3840×2160, 2160×3840.

## Host-run bundled CLI (`image_gen.py`)

Codex ships a full CLI for the OpenAI Images API inside its own skill files. This host can run it directly — deterministic, parameterized, no agent in the loop:

```bash
export IMAGE_GEN="${CODEX_HOME:-$HOME/.codex}/skills/.system/imagegen/scripts/image_gen.py"
# Requires: OPENAI_API_KEY + `pip install openai` (and `pillow` for downscaling)
```

Subcommands: `generate`, `edit`, `generate-batch`. Defaults: model `gpt-image-2`, size `auto`, quality `medium`, format `png`. `--dry-run` prints the API payload without network. Never modify the script.

Key flags:
- `--quality low|medium|high|auto` — all subcommands. `low` for drafts; `medium|high|auto` for finals, dense text, identity edits
- `--size WxH` — within the constraints above
- `--background transparent` — **gpt-image-1.5 only**, with `--output-format png|webp`; not supported by gpt-image-2
- `--input-fidelity low|high` — edit-only, **not for gpt-image-2** (always high-fidelity inputs)
- `--mask <png>` — edit-only, single mask, same size as the image, must have alpha, applies to the first `--image`
- `--image` — repeatable for multi-image edits; order meaningful, label roles in the prompt
- `--n` — variants of one prompt (distinct assets need distinct jobs, not `--n`)
- `--no-augment` — skip prompt restructuring; your prompt goes verbatim
- augmentation fields: `--use-case --style --composition --constraints`
- also: `--prompt-file --output-compression --moderation --max-attempts --fail-fast --force --downscale-max-dim --out-dir`

Batch:

```bash
python "$IMAGE_GEN" generate-batch --input prompts.jsonl --out-dir ./out --concurrency 5
```

JSONL: one job per line — `{"prompt": "...", "size": "1536x1024", "quality": "high", "out": "name.png"}` — per-job overrides for `size quality background output_format n model out` and augmentation fields.

## `remove_chroma_key.py` (transparent cutout helper)

Ships inside Codex at `$CODEX_HOME/skills/.system/imagegen/scripts/remove_chroma_key.py`. Converts a flat chroma-key background to alpha; the host runs it after a Mode A keyed generation (needs Pillow):

```bash
python "${CODEX_HOME:-$HOME/.codex}/skills/.system/imagegen/scripts/remove_chroma_key.py" \
  --input <source.png> --out <final.png> \
  --auto-key border --soft-matte \
  --transparent-threshold 12 --opaque-threshold 220 --despill
```

Flags (verified from argparse): `--input` `--out` (png/webp) · `--key-color #rrggbb` (default `#00ff00`) · `--tolerance 0-255` (hard-key mode) · `--auto-key none|corners|border` (sample key from the image) · `--soft-matte` (smooth alpha ramp) · `--transparent-threshold` / `--opaque-threshold` · `--edge-feather 0-64` (use sparingly) · `--edge-contract N` (shrink matte N px — fixes residual fringe) · `--despill`/`--spill-cleanup` (decontaminate key spill) · `--force`.

Validation after removal: mode RGBA, alpha extrema include 0 and 255, all 4 corner alphas 0, no key-color fringe. Thin fringe → retry with `--edge-contract 1`. Hard tolerance-only mode (no `--soft-matte`) is for flat pixel-art only.

## Cost / usage

- **ChatGPT/Codex subscription**: 1 image turn ≈ 3–5 text turns of usage limit. Limits reset on a clock — the error message names the retry time.
- **API key (host-run CLI)**: per-image billing — image output $30.00 / 1M output tokens, image input $8.00 / 1M input tokens ($2.00 / 1M cached), plus text-input tokens for the prompt (see [OpenAI pricing](https://openai.com/api/pricing/)). Typical per-image cost ~$0.04–$0.35.

For batches of 10+ images, API-key mode is generally cheaper than the subscription.

## Limits

| Limit | Workaround |
|---|---|
| No native transparency on gpt-image-2 | Chroma-key + host-run `remove_chroma_key.py` (default), or host-run CLI `gpt-image-1.5 --background transparent` (complex edges: hair/fur/glass/smoke) |
| No per-call quality/masks/fidelity via codex | Host-run bundled CLI |
| Size must satisfy the pixel-floor / multiple-of-16 rules | Generate valid, host downscales (or `--downscale-max-dim` in CLI) |
| Precise element placement in complex layouts | Labeled layout blocks in the schema; final production typography in SVG/HTML after generation |
| Small non-Latin text (CJK etc.) can break | ≥5% of image height, EXACT TEXT + double quotes, "Hangul syllables not decomposed" for Korean; dense labels → CLI `--quality high` |
| Latency up to 2 min | Bash tool timeout ≥ 300000 ms |
| Non-deterministic across runs | No seed control exposed as of 0.144. Iterate with change-X/preserve-Y instead of rerolling |

## Troubleshooting

### `codex: command not found`
`npm i -g @openai/codex`

### Authentication required
Tell the user: run `! codex login` directly in the Claude Code session.

### `ERROR: You've hit your usage limit ... try again at HH:MM` (verified on 0.144.1)
Subscription quota exhausted — image turns burn it 3–5× faster. Either wait for the stated reset time, or switch to the host-run CLI with `OPENAI_API_KEY` (per-image billing, no subscription quota). Report the reset time to the user rather than silently retrying.

### Hangs on "Reading additional input from stdin..."
Missing `< /dev/null`.

### Agent stalls or asks a question mid-exec
The prompt triggered one of Codex's confirmation gates (usually a model/path downgrade toward gpt-image-1.5 or CLI mode). Use the host-run CLI instead — it has no gates. If you must route through codex, pre-authorize explicitly in the prompt: "I explicitly request the CLI fallback with scripts/image_gen.py and model gpt-image-1.5 ...".

### Codex didn't print a path (Mode A) / no file at expected path (Mode B)
Deterministic fallback: `find ~/.codex/generated_images -name 'ig_*.png' -mmin -3 -type f -print0 | xargs -0 ls -t | head -1` — newest-by-mtime is the one just produced.

### Output is wildly off
1. Fill every schema slot (empty slots = the Codex agent's taste)
2. Strip empty adjectives; name medium/palette/lighting/composition
3. Text work: exact quoted copy + "appears exactly once" + typography/placement/contrast
4. Still off → rewrite Style/medium and Subject slots; don't stack ten corrections in one rerun

### Transparent output came back opaque
Corner alphas of 255 = the removal step never ran. Run `remove_chroma_key.py` on the saved source, or rerun the full chroma-key recipe.

### Same prompt, different result
Expected — no seed control exposed as of 0.144. Iterate with change-X/preserve-Y instead of rerolling.

### Codex CLI was upgraded and `$imagegen` behaves differently
Check `codex --version`. Scan the codex changelog for `imagegen`/`generated_images` mentions — paths and flag semantics are not public contract. Open an issue on this skill's repo with the new behavior.

## Verified vs documentary

Runtime-verified: output-path layout, size-floor behavior (256→1254), the agent-side prompt rewrite (`revised_prompt` in session logs), the usage-limit error, the stdin hang. Documented from Codex's own skill files but not yet independently re-verified end-to-end: the built-in tool exposing no quality/size parameters, and the full chroma-key removal round-trip. If a recipe misbehaves, check those two first and open an issue with findings.
