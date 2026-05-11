---
name: codex-imagegen
description: Generate or edit images via the Codex CLI's built-in `$imagegen` skill (gpt-image-2). Use this skill when the user needs to produce visual assets saved to disk — icons, banners, illustrations, OG images, infographics, diagrams, hero art, placeholder images, or photo edits — in PNG/JPEG/WebP format. Triggers — "generate image", "make an icon", "create a banner", "OG image", "imagegen", "GPT Image 2", "codex image", "이미지 만들어줘", "아이콘 생성", "배너 디자인", or whenever the user wants a visual file written to the local filesystem. Do NOT use for design discussion, image analysis, or screenshot review.
---

# Codex Imagegen

## Overview

Invoke the `$imagegen` skill built into Codex CLI (`codex` v0.130+) to generate images with the **gpt-image-2** model. This skill's job is to (1) write a strong prompt, (2) run `codex exec` non-interactively in the **safer default mode**, (3) move/resize the resulting PNG to where the user wants it.

**Prerequisites**: `codex` CLI installed and logged in (`codex login`). Each image-generation turn consumes Codex usage limits 3–5× faster than a plain text turn. For batch work, set `OPENAI_API_KEY` to switch to per-image API billing.

## Two run modes

This skill defines two modes. **Default to safe mode**; only fall back to automated mode when the user explicitly opts in or batching makes the cost of repeated path-handling unacceptable.

### Mode A — Safe (default)

```bash
codex exec --skip-git-repo-check --sandbox workspace-write \
  '$imagegen <PROMPT>.
Generate the image and then print ONLY the absolute path of the
resulting PNG on the final line of your reply. Do NOT copy, move,
or modify the file.'
```

Then this host (Claude Code) parses the printed path and runs the `cp`/`sips` step itself, in its own approved-tool context.

Why safer: Codex never receives carte-blanche shell access. With `--sandbox workspace-write` and approvals active, the sub-agent's blast radius is significantly reduced — Codex's sandbox still permits writes inside the current workspace, but blocks writes outside it, and elevated operations require approval prompts that, run non-interactively, will fail rather than execute silently. Combined with the prompt instruction to "only generate, do not copy or move," the realistic worst case is far smaller than Mode B's "arbitrary shell in your workspace."

### Mode B — Automated (opt-in, requires trust)

```bash
codex exec --skip-git-repo-check --sandbox workspace-write \
  --dangerously-bypass-approvals-and-sandbox \
  '$imagegen <PROMPT>. Save the final image to <PATH> at exactly WxH pixels.'
```

The `--dangerously-bypass-approvals-and-sandbox` flag lets the Codex sub-agent run arbitrary shell commands (`cp`, `sips`, `find`, anything else) without approval. This is convenient for batch jobs but gives the Codex model real write power in your working directory. Only use it when you trust the prompt source AND the directory you're in. See `SECURITY.md` in the repo for the threat model.

## How to write a good prompt

Full guide in [`references/prompting-guide.md`](references/prompting-guide.md). Core principles:

1. **Front-load the first 50 words** — the model weights the opening more heavily.
2. **Five-part structure** — `Scene → Subject → Details → Use case → Constraints`. Fill every slot.
3. **No keyword soup.** Skip empty adjectives like "stunning, 8K, masterpiece". Brief the model like a photographer.
4. **Wrap literal text in double quotes or ALL CAPS** and add "no extra text, no duplicate text".
5. **For edits, list what to preserve** explicitly: "change only X, keep everything else identical".
6. **State exclusions**: "no watermark, no logo, no extra text, no border".

For complex layouts, in-image text, or edits, read `references/prompting-guide.md` first.

## Workflow (Mode A — default)

### 1. Parse the user request

Fill these five slots from what the user said:

- **Scene/context** — environment, mood, time of day
- **Subject** — what is being depicted
- **Details** — style, medium, lighting, camera, color, texture
- **Use case** — icon? OG card? banner? illustration? (drives size/aspect)
- **Constraints** — text yes/no, color limits, things to forbid

If multiple slots are missing, ask **one** clarifying question targeting the most important gap and proceed with reasonable inferences for the rest.

### 2. Decide the output path

Default — save into the user's current working directory with a meaningful filename: `./assets/icons/dashboard.png`, `./public/og-image.png`, `./hero-banner.png`, etc.

### 3. Compose the prompt (five-part paragraph)

Example:

```
A quiet minimalist illustration for an indie note-taking app's marketing
page. A single seedling with two leaves growing from a flat horizon line,
centered composition, generous whitespace around the subject. Clean
monochrome vector style, 2px black stroke on pure white background.
Use case: hero icon at 512x512 PNG. No text, no shadows, no gradients,
no watermark.
```

### 4. Run codex exec in Mode A

```bash
codex exec --skip-git-repo-check --sandbox workspace-write \
  '$imagegen <PROMPT>.
Generate the image and then print ONLY the absolute path of the
resulting PNG on the final line of your reply. Do NOT copy, move,
or modify the file.'
```

Bash tool timeout: 300000 ms (5 min). Complex prompts can take up to 2 min.

### 5. Parse the path and finish locally

Grep the codex stdout for an absolute path under `~/.codex/generated_images/.*/ig_*\.png`. If parsing fails, the fallback is deterministic:

```bash
find ~/.codex/generated_images -name 'ig_*.png' -mmin -3 -type f -print0 \
  | xargs -0 ls -t | head -1
```

Then this host runs the move/resize itself:

```bash
# Move to the user-requested path
cp "$SRC" ./output.png

# Optional: resize to exact size (sips arg order is HEIGHT WIDTH)
sips -z 512 512 ./output.png            # square
sips -z 900 1600 ./hero-banner.png      # 1600x900 landscape (height 900, width 1600)
```

If running on Linux, replace `sips -z H W` with ImageMagick:
```bash
convert input.png -resize WxH! output.png
```

### 6. Verify visually

Open the resulting PNG with the Read tool. If the output drifts from intent:
- Small drift → follow up with a "change only X, preserve everything else" iteration
- Large drift → rewrite Subject/Details slots and run again

## Workflow (Mode B — opt-in automated)

Use Mode B **only when the user has explicitly asked for the automated / bypass flow**. Do NOT auto-escalate to Mode B based on batch size, "safe directory" inference, or convenience. If the per-image Mode A round-trip feels expensive for a batch, surface that to the user and ask for explicit opt-in before switching modes.

```bash
codex exec --skip-git-repo-check --sandbox workspace-write \
  --dangerously-bypass-approvals-and-sandbox \
  '$imagegen <PROMPT>. Save to ./<output>.png at exactly WxH pixels and print the absolute path.'
```

The Codex sub-agent handles its own `cp`/`sips`. Faster but trades trust boundary — see `SECURITY.md`.

## Common recipes

All recipes default to **Mode A**. Add `--dangerously-bypass-approvals-and-sandbox` only after reading SECURITY.md.

### Icon set (batch)

```bash
codex exec --skip-git-repo-check --sandbox workspace-write \
  '$imagegen Generate 6 monochrome line icons, each 128x128 PNG.
Subjects: home, settings, profile, notifications, search, logout.
Style: 2px black stroke on white background, geometric, centered,
identical visual weight across the set, no text, no fill.
Print the absolute path of each generated PNG on its own line.
Do NOT copy or move the files.'
```

The host then `cp`s each into `./assets/icons/<subject>.png` and `sips -z`s as needed.

### OG image (with text)

```bash
codex exec --skip-git-repo-check --sandbox workspace-write \
  '$imagegen Open Graph image, 1200x630 PNG, for a note-taking app called
"Notable". Layout: large bold sans-serif headline "Notable" top-left,
subtitle "fast notes for fast minds" below it. Right side: soft gradient
blue→white background with a faint seedling silhouette. EXACT TEXT
verbatim, no extra text, no duplicate text, no watermark.
Print the absolute path of the resulting PNG; do not copy or move.'
```

Then host: `cp "$SRC" ./public/og-image.png && sips -z 630 1200 ./public/og-image.png`.

### Edit an existing image

```bash
codex exec -i ./current-banner.png --skip-git-repo-check --sandbox workspace-write \
  '$imagegen Change only the background color from white to deep navy (#0a1f3d).
Preserve everything else identically: logo position, typography, all text
content, composition, lighting direction. Print the absolute path of the
resulting PNG; do not copy or move.'
```

## Resources

- [`references/prompting-guide.md`](references/prompting-guide.md) — gpt-image-2 prompting (5-part structure, text rendering, edit pattern, anti-patterns, multilingual, before/after)
- [`references/cli-reference.md`](references/cli-reference.md) — `codex exec` flags, output path behavior, mode A vs B trade-offs, post-processing, limits, costs, troubleshooting
- [`assets/hero.png`](assets/hero.png) — sample 1600×900 image produced via this skill

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `command not found: codex` | CLI not installed | Tell user: `npm i -g @openai/codex` |
| `Authentication required` | Not logged in | Ask user to run `! codex login` |
| Output size differs from request | gpt-image-2 size adherence is loose | Host runs `sips -z H W` after retrieving the path |
| Transparent background ignored | Per [OpenAI guide](https://developers.openai.com/api/docs/guides/image-generation), gpt-image-2 does not support `background: "transparent"` | Use gpt-image-1.5 via the Image API, or post-process |
| Text garbled or duplicated | Weak text spec | Add EXACT TEXT marker, double quotes, "no duplicate text" |
| Run takes > 2 min | Normal for complex prompts | Bash timeout ≥ 300000 ms |
| Codex didn't print a path in Mode A | Model wandered off instructions | Use deterministic fallback: `find ~/.codex/generated_images -name 'ig_*.png' -mmin -3 -type f -print0 \| xargs -0 ls -t \| head -1` |
| Generic "AI slop" look | Empty adjectives | Replace with concrete details ("overcast daylight, 50mm feel") |
