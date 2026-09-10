---
name: codex-imagegen
description: Create and refine image files from Claude Code using a Codex subscription. Handles short creative interviews, distinct visual directions, reference-based edits, consistent asset sets, and verified transparent PNGs. Use for image generation, imagegen, GPT Image, hero art, product photos, icons, posters, 이미지 생성, 시안, 이미지 수정, or 투명 배경. Exclude image analysis and code-native SVG edits.
---

# Codex Imagegen

Claude directs and reviews; Codex only generates. Use the user's Codex subscription;
never use a separately billed image API. Requires Python 3.9+, macOS/Linux, and
logged-in Codex CLI 0.153.4+ (`codex login`). Resolve `<SKILL_DIR>` from this file.

## Route by intent

| Request | Action | Read only if needed |
|---|---|---|
| Clear request / “just make it” | Generate one image immediately | No extra reference |
| Unclear direction / “interview me” | Ask 1–3 consequential questions together | [interview.md](references/interview.md) |
| “Options”, “시안”, multiple directions | Default to 3 distinct candidates if count is unspecified | [directions.md](references/directions.md) |
| Change an existing image | Inspect it, state change + preserve list, attach it | [editing.md](references/editing.md) |
| Exact text, photography, complex composition | Add only the relevant craft details | [prompting-guide.md](references/prompting-guide.md) |
| Model question or execution failure | Explain verified capability or fix the failure | [cli-reference.md](references/cli-reference.md) |

Do not load every reference, repository documentation, or launcher source. Reuse
answers and relevant project style facts already in context. Read `DESIGN.md` only
when matching this project's style. Do not run Codex to interview, plan, or judge.

## Make the brief

Use the user's language. Specify intended use, subject, medium, framing, light,
palette, and constraints only where they affect this image. Preserve detailed
user direction; omit irrelevant fields. Aim for 80–180 words for a normal image,
shorter for a local edit; exact copy and necessary preservation rules take priority.

```text
$imagegen
Asset: website hero, landscape 16:9, one image
Request: a handmade terracotta cup on pale limestone
Look: editorial product photograph; soft window light from the left;
matte glaze, natural surface imperfections; warm ivory and rust palette
Composition: cup in the right third; quiet empty left half for page copy
Constraints: no text, watermark, border, or extra objects
```

Quote exact text with its placement and one occurrence. For references add
`Image 1: base to edit; Image 2: material reference only` in attachment order.
Send only this final brief and necessary images to Codex, never the conversation,
interview answers, research, this skill, or a whole design document.

## Generate and inspect

Write a UTF-8 brief using the host's file-write tool, then start in the background:

```bash
python3 "<SKILL_DIR>/scripts/image_project.py" --prompt-file "<BRIEF>" --out-dir "<NEW_DIR>" --background
# Attach inputs with --image "<BASE.png>" (repeat in reference order).
```

This returns a job directory immediately. Continue independent requested work;
check later with `image_project.py --out-dir "<DIR>" --status` (no Codex call).
Do not repeatedly poll or claim completion while status is queued/running. Read
completed paths from the manifest, then inspect them. If images are the only work,
wait using the host's background-task mechanism and check at sensible intervals.
Multi-image plans use two workers by default (1–4 configurable); see directions.md.
The underlying `run_codex_imagegen.py` remains available for foreground execution.

The launcher defaults to the lightweight `gpt-5.6-luna` relay with reasoning `none`,
compact relay instructions, no skills catalog, and unrelated tools disabled.
`--model` selects the text relay, NOT an image model. Flare favors speed; Sunburst
favors demanding quality and precise edits. The Codex built-in tool manages its
image backend and this launcher cannot pin either. Do not claim a specific image
model, API quality setting, native 4K, or pixel-perfect preservation was used.

Copy only validated stdout PNG paths to the user's destination or
`output/imagegen/<purpose>/`. Preserve originals; use versioned filenames for edits.
Inspect the image using Claude's image-reading tool at full view and relevant detail.
Check intent, composition, literal text, anatomy/product geometry, preserved details,
and edges. A valid path is not a quality pass. State any visible unresolved defect.

If transparency is requested, run:

```bash
python3 "<SKILL_DIR>/scripts/verify_png_alpha.py" --require-transparent-corners "<PNG>"
```

Use the corners flag for isolated cutouts only. Do not mistake checkerboard pixels
for alpha. See editing.md for transparent edits. Measure actual dimensions before
export; the older 0.153.2 baseline was ≈1.57 MP, not a current resolution guarantee.
Resize proportionally; crop/pad intentionally, never stretch. Label upscaling honestly.

Generate only the requested count. Allow at most one targeted repair per rejected
image; do not automatically polish accepted work, retry timeouts, or rerun a whole
set. User-requested revisions begin a new edit. Return previews, usable file paths,
and one useful next step, such as “pick 2 and tell me what to change.”
