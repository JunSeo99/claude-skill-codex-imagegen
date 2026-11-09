---
name: codex-imagegen
description: Create and refine raster image files (PNG) from Claude Code using the user's Codex subscription. Handles short creative interviews, distinct visual directions, reference-based edits, style-matched asset sets, and verified transparent PNGs. Use whenever the user wants a new or changed bitmap image, such as hero art, product photos, illustrations, posters, app icons, or UI assets; also for imagegen, GPT Image, 이미지 생성, 이미지 시안, 앱 아이콘, 에셋, 이미지 수정, 투명 배경, 画像生成, 生成图片. Not for image analysis, SVG/vector or code-drawn graphics, animation, or code that calls an image API.
---

# Codex Imagegen

Claude directs and reviews; Codex only generates. Use the user's Codex subscription;
never use a separately billed image API. Requires Python 3.9+, macOS/Linux/Windows, and
logged-in Codex CLI 0.164.0+ (`codex login`). On Windows, use `python` or `py` where
this file says `python3`. Resolve `<SKILL_DIR>` from this file.

## Route by intent

| Request | Action | Read only if needed |
|---|---|---|
| Clear request / “just make it” | Generate one image immediately | No extra reference |
| Unclear direction / “interview me” | Ask 1–3 consequential questions together | [interview.md](references/interview.md) |
| “Options”, “시안”, multiple directions | Default to 3 distinct candidates if count is unspecified | [directions.md](references/directions.md) |
| Change an existing image | Inspect it, state change + preserve list, attach it | [editing.md](references/editing.md) |
| A set that must match (icons, UI assets, series) | Settle the style on one sample, then reuse a style lock | [prompting-guide.md](references/prompting-guide.md) |
| Styled art, exact text, photography | Add only the relevant craft details | [prompting-guide.md](references/prompting-guide.md) |
| Model question or execution failure | Run `scripts/codex_status.py` (no model call), then explain or fix | [cli-reference.md](references/cli-reference.md) |

Do not load every reference, repository documentation, or launcher source. Reuse
answers and relevant project style facts already in context. Read `DESIGN.md` only
when matching this project's style. Do not run Codex to interview, plan, or judge.

## Make the brief

Use the user's language. Specify intended use, subject, medium, framing, light,
palette, and constraints only where they affect this image. Preserve detailed
user direction; omit irrelevant fields. For styled or illustrated images, set value
contrast, palette roles, and one focal subject first (prompting-guide.md). Aim for
80–180 words for a normal image, shorter for a local edit; exact copy and necessary
preservation rules take priority.

```text
Asset: website hero for a notes app, landscape 16:9, one image
Request: an open notebook and a few index cards on a clean desk
Look: editorial product photograph; soft window light from the left;
matte paper texture, natural shadows; warm ivory and ink-blue palette
Composition: subject in the right third; quiet empty left half for page copy
Constraints: no readable writing, logos, watermark, border, or extra objects
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
Do not poll repeatedly or claim completion while queued/running. If images are the
only work, wait with the host's background-task mechanism. Read completed paths from
the manifest, then inspect them. Multi-image plans: directions.md. For foreground
execution use `run_codex_imagegen.py`.

The default and recommended relay is `gpt-6-luna` with reasoning `none`, compact
instructions, no skills catalog, and unrelated tools disabled.
Both scripts accept `--model` and `--reasoning-effort` to change it; that is the
text relay, NOT an image model. Codex's server picks the image model, quality, and
size; no flag, brief wording, or output metadata selects or reveals it. Never call
an output a specific GPT Image version or variant; if asked, say Codex chose the
model server-side. Do not claim an API quality setting, native 4K, or pixel-perfect
preservation.

Copy only completed manifest images (or launcher-printed paths) to the user's
destination or `output/imagegen/<purpose>/`. Preserve originals; version edits.
Keep the final brief as `output/imagegen/<purpose>/<image-name>.md`, even when the
PNG goes elsewhere. Never write briefs into the user's
destination; asset folders such as `public/` are often served. Skip confidential briefs.
Inspect the image using Claude's image-reading tool at full view and relevant detail.
Check intent, composition, literal text, anatomy/product geometry, preserved details,
and edges. A valid path is not a quality pass. State any visible unresolved defect.

If transparency is requested, describe only the isolated subject and say
"transparent background" (the relay then sets the tool's `transparent_background`
flag). A described backdrop, floor, or scene can override the flag. Then run:

```bash
python3 "<SKILL_DIR>/scripts/verify_png_alpha.py" "<PNG>"  # add --require-transparent-corners for isolated cutouts
```

If the subject must be fully solid (alpha is often 250–254), write a copy with
`scripts/solidify_png_alpha.py <PNG> <OUT.png>`. Do not mistake checkerboard pixels
for alpha. A cutout of an existing photo is re-rendered: compare labels, text, and
framing with the source (editing.md). Measure actual dimensions before export;
codex-cli 0.153.2–0.166.0 returned ≈1.57 MP, which is not a resolution guarantee.
Resize proportionally; crop/pad intentionally, never stretch. Label upscaling honestly.

Generate only the requested count. Allow at most one targeted repair per rejected
image; do not automatically polish accepted work, retry timeouts, or rerun a whole
set. User-requested revisions begin a new edit. Return previews, usable file paths,
and one useful next step, such as “pick 2 and tell me what to change.”
