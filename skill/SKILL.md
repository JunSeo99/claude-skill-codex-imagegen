---
name: codex-imagegen
description: Generate or edit images via the Codex CLI's built-in `$imagegen` skill (gpt-image-2). Use this skill when the user needs to produce visual assets saved to disk — icons, banners, illustrations, OG images, infographics, diagrams, hero art, placeholder images, transparent-background cutouts, or photo edits — in PNG/JPEG/WebP format. Triggers — "generate image", "make an icon", "create a banner", "OG image", "imagegen", "GPT Image 2", "codex image", "transparent background", "이미지 만들어줘", "아이콘 생성", "배너 디자인", "투명 배경", or whenever the user wants a visual file written to the local filesystem. Do NOT use for design discussion, image analysis, or screenshot review.
---

# Codex Imagegen

## Overview

Invoke the `$imagegen` skill built into Codex CLI (`codex` v0.130+, validated against 0.144.1) to generate images with the **gpt-image-2** model. This skill's job is to (1) translate the user's request into a concrete art direction, (2) write a strong prompt, (3) run `codex exec` non-interactively in the **safer default mode**, and (4) move/resize/post-process the resulting image to where the user wants it.

**Prerequisites**: `codex` CLI installed and logged in (`codex login`). Each image turn consumes Codex subscription usage 3–5× faster than a text turn; for batch work or usage-limit windows, set `OPENAI_API_KEY` and use the host-run CLI path (per-image API billing).

## How your prompt actually flows (read this first)

Your prompt does NOT go to gpt-image-2 verbatim. The Codex agent (an LLM) reads its built-in imagegen skill and **rewrites your prompt into its labeled schema** before calling the model — verified in session logs: the `revised_prompt` sent to gpt-image-2 is the agent's restructured version. Its rewrite policy: a detailed prompt gets *normalized* (no creative additions); a vague prompt gets *augmented* — the agent invents composition, scene detail, and polish from its own defaults. Two consequences:

1. **To keep art-direction control, arrive fully specified.** Every slot you leave empty is a slot the Codex agent fills with its own taste.
2. **Write the prompt in Codex's native schema directly.** Then "normalize" is a no-op and nothing is lost in translation:

```text
Use case: <slug — see list below>
Asset type: <where the asset will be used, final size/aspect>
Primary request: <the main ask in one sentence>
Input images: <Image 1: role; Image 2: role>          (only when attaching images)
Scene/backdrop: <environment, time, mood>
Subject: <main subject; for people: crop, pose, gaze, hands, expression>
Style/medium: <photo / illustration / 3D / print process — the taste level>
Composition/framing: <viewpoint, placement, negative space, hierarchy>
Lighting/mood: <light source, direction, temperature>
Color palette: <3-5 named colors or relationships>
Materials/textures: <surface details, grain, imperfections>
Text (verbatim): "<exact copy>"                        (omit if no text)
Constraints: <must keep / must render exactly once / must not change>
Avoid: <negative constraints, watermark/logo/extra-text bans>
```

Use-case slugs the Codex agent classifies by (using them yourself skips misclassification) —
Generate: `photorealistic-natural` `product-mockup` `ui-mockup` `infographic-diagram` `scientific-educational` `ads-marketing` `productivity-visual` `logo-brand` `illustration-story` `stylized-concept` `historical-scene`.
Edit: `text-localization` `identity-preserve` `precise-object-edit` `lighting-weather` `background-extraction` `style-transfer` `compositing` `sketch-to-render`.

Full prompting guide (first-50-words rule, text rendering, people, edits, anti-patterns, Korean text): [`references/prompting-guide.md`](references/prompting-guide.md).

## Two run modes

**Default to Mode A**; use Mode B only when the user explicitly opts in. Do NOT auto-escalate based on batch size, "safe directory" inference, or convenience — if Mode A round-trips feel expensive for a batch, surface that and ask.

### Mode A — Safe (default)

```bash
codex exec --skip-git-repo-check --sandbox workspace-write \
  '$imagegen <PROMPT>.
Generate the image and then print ONLY the absolute path of the
resulting PNG on the final line of your reply. Do NOT copy, move,
or modify the file.' < /dev/null
```

Then this host (Claude Code) parses the printed path and runs the `cp`/resize/post-processing itself, in its own approved-tool context.

Why safer: Codex never receives carte-blanche shell access. With the sandbox and approvals active, writes outside the workspace are blocked and elevated operations fail rather than execute silently. See `SECURITY.md` for the threat model.

### Mode B — Automated (opt-in, requires trust)

```bash
codex exec --skip-git-repo-check --sandbox workspace-write \
  --dangerously-bypass-approvals-and-sandbox \
  '$imagegen <PROMPT>. Save the final image to <PATH> at exactly WxH pixels and print the absolute path.' < /dev/null
```

`--dangerously-bypass-approvals-and-sandbox` lets the Codex sub-agent run arbitrary shell (`cp`, `sips`, python helpers) without approval. Convenient for one-shot batches; a real trust hand-off. Read `SECURITY.md` before using.

Both modes: wrap `$imagegen` in **single quotes**; append **`< /dev/null`** (codex exec otherwise hangs waiting on stdin); Bash timeout ≥ **300000 ms**.

## Execution controls: what each path can actually do

The built-in `image_gen` tool exposes **no per-call API parameters** — quality, masks, `input_fidelity`, and output format are CLI-only controls per Codex's own skill files. Writing "use quality high" in a Mode A/B prompt is prose the agent cannot act on. The CLI here means the script bundled inside Codex (`$CODEX_HOME/skills/.system/imagegen/scripts/image_gen.py`), which **this host can run directly** — no codex agent turn, no Mode B needed. It requires `OPENAI_API_KEY` and the `openai` Python package.

| You need | Mode A/B (codex, subscription) | Host-run bundled CLI (`OPENAI_API_KEY`) |
|---|---|---|
| Quality control | ✗ — accept default | `--quality low\|medium\|high\|auto` |
| Exact pixel size | host resizes after (Mode A) / agent resizes (Mode B) | `--size WxH` honored within constraints |
| Transparent background | chroma-key generation + host-run removal helper | `gpt-image-1.5 --background transparent` |
| Masked edit / `input_fidelity` | ✗ | edit-only flags (`input_fidelity` not for gpt-image-2) |
| Many assets | one codex turn, one `image_gen` call per asset | `generate-batch` JSONL + `--concurrency` |
| Verbatim prompt (no rewrite) | ✗ — agent always restructures | `--no-augment` |
| Billing | subscription quota (3–5×/image) | per-image API (~$0.04–$0.35) |

**gpt-image-2 size constraints** (deterministic, not "loose adherence"): edges multiples of 16, max edge 3840, ratio ≤ 3:1, **total pixels 655,360–8,294,400**, above 2560×1440 experimental. A 256×256 request violates the pixel floor — that is why small icons come back ~1254×1254. Generate at a valid size (e.g. 1024×1024) and downscale on the host.

## Workflow (Mode A — default)

### 1. Parse the request into the schema

Fill the native-schema slots from what the user said. If a critical slot is missing (subject, use case, text copy), ask **one** clarifying question targeting the most important gap; infer opinionated defaults for minor gaps. Avoid bland defaults ("modern clean", "minimal", "sleek") unless backed by concrete visual choices — they are exactly what the Codex agent's augmentation produces on its own.

### 2. Decide the output path

Default: current working directory, meaningful filename — `./public/og-image.png`, `./assets/icons/dashboard.png`, `./<purpose>-<descriptor>.png`.

### 3. Quality preflight

- **Could a junior designer produce a specific comp from this brief?** If not, add concrete layout, material, color, lighting decisions.
- **Generic AI aesthetics?** Remove glossy gradients, floating shapes, fake dashboards, stock smiles, empty adjectives.
- **Text is the deliverable?** Exact copy in quotes, placement, typography, contrast, "appears exactly once". Dense/small text garbling at default quality → host-run CLI with `--quality high`, not prose.
- **People?** Crop, body scale, gaze, pose, hands, object contact, skin texture, "no heavy retouching / no plastic skin".
- **Transparency?** Follow the decision tree below — do not improvise post-processing.
- **Reference available?** For brand/product/venue/food styles, attach a reference (`-i`) and label its role instead of describing from memory.

### 4. Run codex exec in Mode A

As in "Two run modes". For edits attach inputs with repeatable `-i <file>` and label each by index and role in the prompt.

### 5. Parse the path and finish locally

Grep stdout for an absolute path under `~/.codex/generated_images/.*/ig_*.png`. Deterministic fallback if parsing fails:

```bash
find ~/.codex/generated_images -name 'ig_*.png' -mmin -3 -type f -print0 | xargs -0 ls -t | head -1
```

Then the host moves/resizes:

```bash
cp "$SRC" ./output.png
sips -z 512 512 ./output.png          # macOS resize (args are HEIGHT WIDTH)
# Linux: convert input.png -resize WxH! output.png
```

### 6. Verify visually

Open the PNG with the Read tool. Reject on: generic AI gloss, weak composition, wrong/duplicate text, wrong aspect, unwanted border/background. Iterate with **one change per pass**, restating the full preserve list every time — the model drifts silently when you stop repeating invariants.

## Transparent backgrounds — decision tree

gpt-image-2 does not support `background=transparent`. Pick by subject and constraints:

1. **Default — chroma-key + host-run removal (no API key).** Generate the subject on a perfectly flat solid key color via Mode A, then the host converts key to alpha with the helper shipped inside Codex. Works for **white subjects too** (paper, ceramic, white characters) because the key color, not whiteness, defines the background.
2. **True native alpha — host-run CLI `gpt-image-1.5 --background transparent`** (requires `OPENAI_API_KEY`). Use when edges are genuinely hard: hair, fur, feathers, smoke, glass, liquids, translucent/reflective materials, soft shadows — or when chroma-key validation fails.
3. **Exact geometry/palette (icon families, brand marks)** → skip imagegen; the host draws with Pillow on an RGBA canvas. Exact hex, exact size, zero drift.
4. **Legacy opaque PNG you cannot regenerate** → removal helper with `--key-color` matched to the flat background. White background + white subject content is inherently ambiguous — expect bleed; prefer regenerating via path 1.

## Common recipes

All recipes default to **Mode A**.

### Standard generation (native schema)

```bash
codex exec --skip-git-repo-check --sandbox workspace-write \
  '$imagegen
Use case: logo-brand
Asset type: app hero icon, final 512x512 PNG
Primary request: a restrained editorial line icon of a single seedling
Scene/backdrop: generous white margin, flat horizon line
Subject: one seedling with two asymmetric leaves, centered slightly below optical middle
Style/medium: high-end newspaper spot illustration, monochrome ink
Composition/framing: centered, low placement, generous negative space
Color palette: single charcoal ink on white
Materials/textures: varied 2-3px stroke weight, subtle hand-drawn curvature, no fill
Constraints: no text, no shadows, no gradients
Avoid: watermark, border, clip-art look

Generate the image and then print ONLY the absolute path of the resulting PNG
on the final line of your reply. Do NOT copy, move, or modify the file.' < /dev/null
```

Host: `cp "$SRC" ./assets/seedling-icon.png && sips -z 512 512 ./assets/seedling-icon.png`.

### Transparent cutout (chroma-key, no API key)

```bash
codex exec --skip-git-repo-check --sandbox workspace-write \
  '$imagegen Create <subject description> on a perfectly flat solid #00ff00 chroma-key
background for background removal. The background must be one uniform color with no
shadows, gradients, texture, reflections, floor plane, or lighting variation. Keep the
subject fully separated with crisp edges and generous padding. Do not use #00ff00
anywhere in the subject. No cast shadow, no reflection, no watermark, no text.
Print ONLY the absolute path of the resulting PNG. Do NOT copy, move, or modify it.' < /dev/null
```

Host removes the background (helper ships inside Codex; needs Pillow):

```bash
python "${CODEX_HOME:-$HOME/.codex}/skills/.system/imagegen/scripts/remove_chroma_key.py" \
  --input "$SRC" --out ./asset.png \
  --auto-key border --soft-matte --transparent-threshold 12 --opaque-threshold 220 --despill
```

Validate: mode RGBA, alpha extrema include 0 and 255, all 4 corner alphas 0, no green fringe. Thin fringe → retry with `--edge-contract 1`. Green subject → key `#ff00ff` instead; never use a key color present in the subject.

### True native transparency (host-run CLI, gpt-image-1.5)

```bash
# Requires: OPENAI_API_KEY + `pip install openai`
export IMAGE_GEN="${CODEX_HOME:-$HOME/.codex}/skills/.system/imagegen/scripts/image_gen.py"
python "$IMAGE_GEN" generate --model gpt-image-1.5 \
  --background transparent --output-format png --quality high \
  --prompt "<subject description>. No text, no watermark, no border." \
  --out ./asset.png
```

Same RGBA validation as above. No codex agent involved — no Mode B, no confirmation gates. (Routing this through codex instead requires Mode B plus an explicit "I request the CLI fallback with gpt-image-1.5" sentence in the prompt, because Codex refuses to downgrade models without explicit user opt-in and `codex exec` has no human to confirm.)

### OG image (with text)

```bash
codex exec --skip-git-repo-check --sandbox workspace-write \
  '$imagegen
Use case: ads-marketing
Asset type: Open Graph card, final 1200x630 PNG
Primary request: OG image for a note-taking app called "Notable"
Scene/backdrop: white left half, pale blue field (#E8F2FF) right half
Subject: quiet editorial ink illustration of a seedling, thin navy linework (#0A1F3D)
Style/medium: restrained editorial print, no abstract blobs, no fake dashboard
Composition/framing: text block top-left at 8% padding, illustration center-right with breathing room
Color palette: white, #0A1F3D navy, #E8F2FF pale blue, medium gray
Text (verbatim): headline "Notable" bold sans-serif ~80px equivalent, appears exactly once; subhead "fast notes for fast minds" ~32px medium gray, appears exactly once
Constraints: high contrast text, unobstructed by objects
Avoid: extra text, duplicate text, logo, watermark, stock photo elements

Print ONLY the absolute path of the resulting PNG. Do NOT copy, move, or modify it.' < /dev/null
```

Host: `cp "$SRC" ./public/og-image.png && sips -z 630 1200 ./public/og-image.png`. If small/dense text garbles, rerun via host-run CLI with `--quality high`.

### Icon set (batch)

```bash
codex exec --skip-git-repo-check --sandbox workspace-write \
  '$imagegen Generate 6 monochrome line icons, each on its own 1024x1024 PNG.
Subjects: home, settings, profile, notifications, search, logout.
Style: coherent product icon family, 2px black stroke on white, geometric but not
clip-art, identical visual weight and optical padding across the set, no text, no fill.
Print the absolute path of each generated PNG on its own line.
Do NOT copy or move the files.' < /dev/null
```

Host `cp`s each into `./assets/icons/<subject>.png` and resizes. For 10+ assets, prefer the host-run CLI `generate-batch` (JSONL, `--concurrency 5`, per-image billing) — see `references/cli-reference.md`.

### Edit / multi-image compositing

```bash
codex exec -i ./base.png -i ./style-ref.png --skip-git-repo-check --sandbox workspace-write \
  '$imagegen
Use case: compositing
Input images: Image 1: base scene to edit — preserve framing and lighting; Image 2: style reference only, do not copy content
Primary request: change only the background color from white to deep navy (#0a1f3d), adopting the paper grain of Image 2
Constraints: preserve everything else identically — logo position, typography, all text content, composition, lighting direction
Avoid: any other change, watermark

Print ONLY the absolute path of the resulting PNG. Do NOT copy, move, or modify it.' < /dev/null
```

`-i` is repeatable; order is meaningful. **Label every image by index and role** — an unlabeled image may be treated as an edit target instead of a reference. One change per pass; restate the full preserve list every iteration.

### Character consistency across a set

The first accepted image is the anchor. In every subsequent prompt, attach it (`-i anchor.png`, labeled "Image 1: character reference — keep identity exactly") and repeat the anchor's identity details verbatim ("same face, same green hooded tunic, same proportions, same palette"). Consistency comes from repetition, not from "same style as before".

### Photorealistic person

Write a documentary photo brief: `photorealistic` stated directly; crop and body geometry (waist-up, both hands visible and correctly gripping objects); gaze direction; real skin texture (pores, smile lines, loose hair strands); worn fabric; lens and light ("eye-level 50mm documentary photo, soft window light from camera-right"); realism guards "honest and unposed, no heavy retouching, no plastic skin, no extra fingers". Identity-sensitive work → host-run CLI `--quality high`.

## Resources

- [`references/prompting-guide.md`](references/prompting-guide.md) — native schema, first-50-words, text rendering, people, edit pattern, multi-image, anti-patterns, Korean text
- [`references/cli-reference.md`](references/cli-reference.md) — Mode A/B flags, host-run bundled CLI (`image_gen.py`), `remove_chroma_key.py` flags, size/cost/limits, troubleshooting
- [`assets/hero.png`](assets/hero.png) — sample 1600×900 image produced via this skill

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `command not found: codex` | CLI not installed | `npm i -g @openai/codex` |
| `Authentication required` | Not logged in | Ask user to run `! codex login` |
| `ERROR: You've hit your usage limit... try again at HH:MM` | Subscription quota exhausted (image turns burn 3–5×) | Wait for the stated reset, or switch to the host-run CLI with `OPENAI_API_KEY` (per-image billing) |
| Codex hangs on "Reading additional input from stdin..." | `codex exec` reads stdin in automation | Append `< /dev/null` |
| Codex didn't print a path (Mode A) | Model wandered off instructions | `find ~/.codex/generated_images -name 'ig_*.png' -mmin -3 -type f -print0 \| xargs -0 ls -t \| head -1` |
| Output size differs from request | Requested size violates gpt-image-2 constraints (usually the 655,360-pixel floor) | Generate valid, host resizes (`sips -z H W` / `convert -resize WxH!`) |
| "quality high" had no effect | Quality is a CLI-only control; Mode A/B has no such parameter | Host-run CLI with `--quality high` |
| Transparent output came back opaque | Removal step skipped, or prompt asked gpt-image-2 for native alpha | Chroma-key recipe + host removal; corner alpha 255 = removal missing |
| Green/magenta fringe on cutout edges | Chroma spill survived removal | `--despill`, then `--edge-contract 1`; `--edge-feather 0.25` only for stair-stepped edges on non-reflective subjects |
| White subject content eaten during cutout | White-background removal on a white-containing subject | Regenerate via chroma-key (key ≠ white) or gpt-image-1.5 native alpha |
| Text garbled or duplicated | Weak text spec, or density beyond default quality | Exact quoted copy + "appears exactly once" + typography/contrast; still failing → CLI `--quality high` |
| Generic "AI slop" look | Empty slots let the Codex agent augment with generic defaults | Fill every schema slot; name medium, palette, lighting, composition |
| Person looks fake | Missing body mechanics / realism guards | Crop, gaze, hands, object contact, skin texture, "no plastic skin" |
| Agent asks a question / stalls mid-exec | Prompt hit a Codex confirmation gate (model/path downgrade) with no human present | Use the host-run CLI instead; or pre-authorize explicitly in the prompt |
| Run takes > 2 min | Normal for complex prompts | Bash timeout ≥ 300000 ms |
