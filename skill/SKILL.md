---
name: codex-imagegen
description: Generate or edit images via the Codex CLI's built-in `$imagegen` skill (gpt-image-2). Use this skill when the user needs visual assets saved to disk — icons, banners, illustrations, OG images, infographics, diagrams, hero art, placeholder images, transparent-background cutouts, or photo edits — in PNG/JPEG/WebP format. Triggers include "generate image", "make an icon", "create a banner", "OG image", "imagegen", "GPT Image 2", "codex image", "transparent background", "이미지 만들어줘", "아이콘 생성", "배너 디자인", and "투명 배경". Do not use for design discussion, image analysis, or screenshot review.
---

# Codex Imagegen

## Overview

Invoke Codex CLI's built-in `$imagegen` skill to generate images with **gpt-image-2**. Translate the request into a concrete art direction, run the bundled safe launcher, move or post-process only a validated generated PNG, and visually verify the final asset.

Prerequisites:

- `codex` CLI v0.149 or newer, installed and logged in with `codex login`
- macOS or Linux
- Python 3.9 or newer, available as `python3`

## Prompt flow

The Codex agent rewrites prompts into a labeled schema before calling gpt-image-2. A detailed prompt is normalized; a vague prompt is augmented with the agent's own choices. Fill every relevant slot to keep control:

```text
$imagegen
Use case: <slug>
Asset type: <where the asset will be used, final size/aspect>
Primary request: <main ask in one sentence>
Input images: <Image 1: role; Image 2: role>          (only for edits/references)
Scene/backdrop: <environment, time, mood>
Subject: <main subject; for people: crop, pose, gaze, hands, expression>
Style/medium: <photo, illustration, 3D, print process>
Composition/framing: <viewpoint, placement, negative space, hierarchy>
Lighting/mood: <source, direction, temperature>
Color palette: <3-5 named colors or relationships>
Materials/textures: <surface details, grain, imperfections>
Text (verbatim): "<exact copy>"                        (omit if no text)
Constraints: <must keep, must render exactly once, must not change>
Avoid: <watermark, logo, extra text, unwanted styles>
```

Generate use-case slugs: `photorealistic-natural`, `product-mockup`, `ui-mockup`, `infographic-diagram`, `scientific-educational`, `ads-marketing`, `productivity-visual`, `logo-brand`, `illustration-story`, `stylized-concept`, `historical-scene`.

Edit use-case slugs: `text-localization`, `identity-preserve`, `precise-object-edit`, `lighting-weather`, `background-extraction`, `style-transfer`, `compositing`, `sketch-to-render`.

For detailed prompting guidance, read [`references/prompting-guide.md`](references/prompting-guide.md).

## Safe execution

Always use [`scripts/run_codex_imagegen.py`](scripts/run_codex_imagegen.py) for the Codex subscription path. The launcher:

- passes the prompt to `codex exec` over stdin through a subprocess argument array, never through shell interpolation;
- uses an ephemeral session in an empty temporary working directory and a read-only sandbox;
- ignores user configuration and project rules, and disables shell, unified execution, hooks, plugins, apps, browser, computer-use, and multi-agent tools;
- passes only a small allowlist of non-secret environment variables required for Codex login and runtime discovery;
- constrains the final response with a JSON schema;
- accepts only existing, non-symlink PNG paths canonically located under `$CODEX_HOME/generated_images/` (default `~/.codex/generated_images/`).

Execution procedure:

1. Write the complete `$imagegen` brief to a temporary UTF-8 text file with the host's file-write tool. Do not construct it with `echo`, `printf`, a shell variable, or a quoted command string.
2. Run the launcher from the installed skill directory:

```bash
python3 "<SKILL_DIR>/scripts/run_codex_imagegen.py" \
  --prompt-file "<PROMPT_FILE>"
```

For edits or references, repeat `--image` in role order:

```bash
python3 "<SKILL_DIR>/scripts/run_codex_imagegen.py" \
  --prompt-file "<PROMPT_FILE>" \
  --image "./base.png" \
  --image "./style-reference.png"
```

Treat only the launcher's stdout lines as source PNG paths. The launcher reads only the schema-constrained final response and refuses missing, non-PNG, symlinked, or out-of-root paths. Never bypass this validation and never run Codex without these restrictions.

## Control surfaces

| Need | Sandboxed Codex subscription path |
|---|---|
| Quality control | No launcher flag; describe the intended finish and visually verify |
| Exact pixel size | Generate at a valid size, then resize in the host context |
| Transparent background | Request genuine alpha in the brief, then run `verify_png_alpha.py` |
| Masked edit / `input_fidelity` | Not exposed; attach role-labeled reference images instead |
| Many assets | Run one image-generation call per distinct asset |
| Verbatim prompt | Not exposed; the Codex image agent normalizes the brief |
| Billing | Codex subscription quota; this skill does not switch to API billing |

gpt-image-2 size constraints are deterministic: edges must be multiples of 16, max edge 3840, long:short ratio at most 3:1, and total pixels 655,360-8,294,400. Generate a small icon at a valid size such as 1024×1024, then downscale on the host.

## Workflow

### 1. Parse the request

Fill the native-schema slots from the user's request. Ask one clarifying question only when a critical item such as subject, required text, or edit target is missing. Infer concrete defaults for minor gaps.

### 2. Choose the output path

Use a meaningful path in the current project, such as `./public/og-image.png`, `./assets/icons/dashboard.png`, or `./<purpose>-<descriptor>.png`.

### 3. Preflight the brief

- Replace empty adjectives such as "modern", "clean", and "stunning" with specific layout, medium, palette, lighting, and material decisions.
- Put exact text in quotes, specify placement and contrast, and require it to appear exactly once.
- For people, specify crop, body scale, gaze, pose, hands, object contact, skin texture, lens, and light.
- Attach brand, product, venue, or style references instead of describing them from memory.
- Follow the transparent-output workflow below.

### 4. Generate safely

Write the prompt file and run the bundled launcher. For multiple inputs, label every image by index and role in the prompt and pass `--image` in the same order.

### 5. Finish locally

Copy or resize the validated source PNG in the host's approved tool context. On macOS, `sips -z` uses height then width:

```bash
cp "$SRC" ./output.png
sips -z 512 512 ./output.png
# Linux: convert input.png -resize WxH! output.png
```

### 6. Verify visually

Open the result with the host's image viewer. Reject generic AI gloss, weak composition, wrong or duplicated text, incorrect aspect, and unwanted borders or backgrounds. Iterate with one change per pass and restate every invariant.

## Transparent backgrounds

GPT Image 2 supports transparent backgrounds in preview. In the Codex built-in path, request the property explicitly in the image brief and verify the returned pixels; do not infer transparency from how a viewer renders the image.

Transparent-output prompt core:

```text
$imagegen
Use case: background-extraction
Asset type: transparent PNG cutout
Primary request: Create <subject> as one isolated asset.
Background: genuinely transparent with a real alpha channel.
Composition/framing: generous transparent padding; subject does not touch the canvas edges.
Constraints: fully transparent canvas corners; preserve smooth anti-aliased edge alpha.
Avoid: checkerboard pattern, white or colored matte, floor plane, cast shadow, reflection,
border, text, or watermark.
```

After generation, require actual transparent and opaque pixels, plus transparent canvas corners:

```bash
python3 "<SKILL_DIR>/scripts/verify_png_alpha.py" \
  --require-transparent-corners "$SRC"
```

The validator reports dimensions, alpha range, transparent/partial/opaque pixel counts, and corner alpha without third-party packages. Visually inspect hair, fur, glass, smoke, and soft edges after it passes. If the result is opaque, retry once with the prompt core above. Do not call a white canvas or painted checkerboard transparent, and do not weaken the launcher or silently switch billing paths.

## Recipe notes

### OG images and text

Use `ads-marketing`. Specify the final aspect, text block coordinates or padding, typography scale, exact quoted strings, contrast, and "appears exactly once". For dense or small text, overlay production typography in HTML/SVG after generation.

### Batch icon sets

Keep every asset at the same valid generation size, stroke weight, optical padding, palette, and medium. Generate each distinct asset with its own brief and launcher call.

### Edits and compositing

State one change per pass and list everything that must remain identical. Label roles explicitly:

```text
$imagegen
Use case: compositing
Input images: Image 1: base scene to edit — preserve framing and lighting;
Image 2: style reference only — do not copy its content
Primary request: change only the background color from white to deep navy (#0a1f3d),
adopting the paper grain of Image 2
Constraints: preserve logo position, typography, all text, composition, and lighting direction
Avoid: any other change, watermark, extra text
```

### Character consistency

Use the first accepted image as the anchor. Attach it in every later prompt, label it as the identity reference, and repeat the same face, clothing, proportions, and palette verbatim.

### Photorealistic people

Write a documentary photo brief with crop, body geometry, gaze, pose, hands, object contact, real skin texture, worn fabric, lens, and light direction. Add "honest and unposed, no heavy retouching, no plastic skin, no extra fingers."

## Resources

- [`scripts/run_codex_imagegen.py`](scripts/run_codex_imagegen.py) — safe subprocess launcher and generated-path validator
- [`scripts/verify_png_alpha.py`](scripts/verify_png_alpha.py) — dependency-free PNG alpha and transparent-corner validator
- [`references/prompting-guide.md`](references/prompting-guide.md) — prompting schema, text, people, edits, multi-image consistency, and anti-patterns
- [`references/cli-reference.md`](references/cli-reference.md) — launcher details, output validation, transparency checks, size rules, and troubleshooting
- [`assets/hero.png`](assets/hero.png) — sample 1600×900 output

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `codex CLI was not found on PATH` | CLI not installed | `npm i -g @openai/codex` |
| Authentication required | Not logged in | Ask the user to run `codex login` directly |
| Usage-limit error with retry time | Subscription quota exhausted | Report the reset time |
| Launcher rejects the prompt file | Empty file, unreadable file, or missing `$imagegen` | Write a UTF-8 file containing the full image brief |
| Launcher rejects the output path | Codex did not return an existing generated PNG in the trusted root | Do not copy another path; rerun once or inspect Codex stderr |
| Output size differs | Requested size violates model constraints | Generate at a valid size and resize on the host |
| "quality high" had no effect | Quality is not exposed as a launcher parameter | Describe the intended finish and visually verify |
| Transparent output is opaque | The model did not honor the alpha requirement | Retry once with the transparent-output prompt core and validate pixels again |
| Alpha passes but edges look poor | Fine semi-transparent detail was rendered badly | Retry one targeted edge correction while preserving all other invariants |
| Text is garbled or duplicated | Brief lacks exact text rules or is too dense | Quote exact copy, require one occurrence, or use an HTML/SVG overlay |
| Generic AI appearance | Too many prompt slots were left vague | Specify medium, palette, lighting, composition, and materials |
| Run exceeds five minutes | Complex generation or stalled agent | Let the launcher time out, report it, and do not weaken the sandbox |
