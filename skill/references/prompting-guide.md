# gpt-image-2 Prompting Guide

Read this before complex images, images containing text, people, or edit operations. Based on OpenAI's GPT Image prompting guide, the Codex CLI built-in imagegen skill (v0.144), and direct verification against session logs.

## Table of contents

1. How the Codex agent reprocesses your prompt
2. The native schema (write in it directly)
3. The first-50-words rule
4. Taste and specificity checklist
5. Text rendering
6. People and photorealism
7. Editing (change-X / preserve-Y pattern)
8. Multi-image references and character consistency
9. Size, aspect, quality — what is actually controllable
10. Anti-patterns
11. Multilingual (Korean text)
12. Before/After examples

---

## 1. How the Codex agent reprocesses your prompt

Verified in session logs: the prompt you pass to `codex exec '$imagegen ...'` is rewritten by the Codex agent before it reaches gpt-image-2. The `revised_prompt` actually sent to the model is a restructured, labeled spec — the agent's own schema — with your details slotted in and constraints tightened.

The agent's rewrite policy (its "specificity policy"):

- **Detailed prompt** → *normalized* into the schema. No creative additions. Your wording survives.
- **Generic prompt** → *augmented*. The agent adds composition, scene concreteness, and polish level from its own defaults. It is forbidden from inventing characters, brands, or slogans — but everything else (palette, mood, framing) is fair game.

Practical rule: **the amount of taste you delegate to the Codex agent equals the number of slots you leave empty.** This is why the guide below insists on filling every slot — not superstition, but who-decides.

## 2. The native schema (write in it directly)

Writing your prompt in the agent's own schema makes normalization a no-op — maximum fidelity between what you wrote and what the model sees:

```text
Use case: <slug>
Asset type: <where it will be used, final size/aspect>
Primary request: <one-sentence main ask>
Input images: <Image 1: role; Image 2: role>          (only with attachments)
Scene/backdrop: <environment, time, mood>
Subject: <main subject>
Style/medium: <medium, visual tradition, production method, taste level>
Composition/framing: <viewpoint, placement, negative space, what the eye lands on first>
Lighting/mood: <source, direction, temperature>
Color palette: <3-5 named colors or relationships>
Materials/textures: <surface details, grain, imperfections>
Text (verbatim): "<exact copy>"
Constraints: <must keep / render exactly once / must not change>
Avoid: <bans: watermark, logo, extra text, border, ...>
```

The old six-slot mental model (Art direction → Scene → Subject → Details → Use case → Constraints) maps 1:1 onto this — the schema is just its Codex-native serialization. `Style/medium` carries the art direction; `Constraints`/`Avoid` are where mediocre prompts fail silently: leave them empty and watermarks, logos, and stray text show up.

If you need the model to see your exact words with **zero** rewriting, the only true bypass is the host-run bundled CLI with `--no-augment` (see `cli-reference.md`).

## 3. The first-50-words rule

The model weights the beginning of the prompt most heavily. Within any free-text field — and in the overall ordering —

- **Front**: style, subject, mood (the elements that must not be lost)
- **Back**: background objects, color accents, secondary detail

Same vocabulary, placed earlier, is reflected more strongly. Don't bury the main subject at the end of a paragraph.

## 4. Taste and specificity checklist

A prompt is not ready if it could describe hundreds of unrelated images.

**Add concrete choices for**:
- **Composition**: centered, rule-of-thirds, low horizon, tight crop, overhead, symmetrical, negative-space direction
- **Medium/process**: editorial photo, documentary photo, gouache, risograph, ink wash, clay render, paper cutout, 1990s magazine scan
- **Lighting**: overcast window light, hard noon shadow, softbox camera-left, backlit rim, fluorescent office light
- **Palette**: 3-5 named colors or relationships — not "vibrant" or "modern"
- **Texture/material**: matte paper grain, brushed steel, linen, ceramic glaze, halftone, imperfect ink edges
- **Hierarchy**: what is largest, what is secondary, where the eye lands first
- **People mechanics**: crop, body scale, gaze, pose, hands, feet if visible, object contact, expression

**Avoid by default**: glossy abstract gradients, floating translucent shapes, fake UI dashboards, generic tech glow, stock-photo business people, plastic skin, over-smoothed 3D, arbitrary bokeh — and "modern", "clean", "sleek", "premium", "stunning", "cinematic" without concrete visual decisions behind them.

Use imagegen when text belongs *inside* the image (posters, menus, signs, ads, infographics, mockups, labels, slides, realistic scenes). Use deterministic HTML/SVG/CSS only when the final asset must remain editable, perfectly typeset, or brand-system compliant.

## 5. Text rendering

gpt-image-2 renders in-image text reliably (including non-Latin scripts), but it rewards exact specification.

**Rules**:
- Wrap literal strings in **double quotes** or ALL CAPS: `headline reads "InSeoul.ai"`
- Add an `EXACT TEXT verbatim` marker
- State typography: weight, size relative to image, placement, contrast (`black text on matte white, unobstructed`)
- Spell tricky words (brand names, proper nouns) **letter-by-letter**: `the word "InSeoul" (I-n-S-e-o-u-l)`
- **Always include**: `appears exactly once`, `no extra text`, `no duplicate text`, `no captions`
- Small text, dense labels, infographics, menus, packaging, multi-font layouts: quality matters, and quality is **CLI-only** — route via the host-run bundled CLI with `--quality high` (see §9). Prose "use quality high" on the built-in path does nothing.
- If the first result is almost right, iterate with only text/layout corrections; do not rewrite the whole art direction.

## 6. People and photorealism

Write a real photo brief, not a subject label.

- Use the word `photorealistic` directly to engage realism mode.
- Specify crop and body geometry: `full body visible, feet included` / `waist-up` / `hands naturally gripping the handlebars`.
- Specify gaze and action: `looking down at the open book, not at camera`.
- Demand real texture and imperfections: pores, wrinkles, flyaway hair, worn fabric, uneven daylight.
- Block glamor defaults: `honest and unposed, no heavy retouching, no plastic skin, no extra fingers`.
- Close-up portraits and identity-sensitive edits benefit from the host-run CLI with `--quality high`.

**Good**:
```
Photorealistic candid waist-up portrait of a Korean cafe owner in her late 30s behind
a small espresso bar, looking slightly camera-left while wiping a ceramic cup. Both
hands visible and correctly gripping the cup and towel. Real skin texture with pores
and subtle smile lines, loose hair strands, cotton apron with worn fabric texture.
Eye-level 50mm documentary photo, soft window light from camera-right, natural color
balance. Honest and unposed, no heavy retouching, no plastic skin, no extra fingers.
```

## 7. Editing (change-X / preserve-Y pattern)

The most common failure mode when attaching an image with `-i`.

1. **Narrow the change to a single target**: "change only the background color"
2. **List the preserve set explicitly**: face/identity, body shape, pose, lighting direction, framing, all text content, geometry, background objects
3. **Repeat the preserve list every iteration** — the model drifts silently when you stop restating it
4. **One change per pass**: "make lighting warmer" → confirm → "remove extra tree"

**Bad**: `Make this better and more professional looking`

**Good**:
```
Change only the sky from overcast to clear blue with soft cumulus clouds. Preserve
everything else identically: the woman's face, pose, beige sweater, the painting on
the wall, marble floor, lighting on her skin (still soft afternoon side-light from
camera-left), camera angle, framing, all texture detail. Match cloud lighting to the
existing skin lighting direction.
```

## 8. Multi-image references and character consistency

The GPT Image family accepts multiple input images (up to 16 in edit workflows). The failure mode is role confusion — the agent treating a style reference as an edit target or vice versa.

- **Label every input by index and role**: `Image 1: base scene to edit — preserve framing; Image 2: jacket style reference only, do not copy content`.
- Describe the interaction explicitly: `place the subject from Image 2 into Image 1`, `apply Image 2's palette to Image 1`.
- `-i` order is meaningful; in CLI edit mode, a `--mask` applies to the first image only (mask must be same size, with alpha).
- **Style transfer**: don't say "same style as the reference" — name the style's visual parts (`chunky pixel forms, limited arcade palette, clean silhouette edges`).
- **Character consistency across a set**: the first accepted image is the anchor. Attach it (`Image 1: character reference — keep identity exactly`) and repeat the identity details verbatim in every prompt: `same face, same green hooded tunic, same proportions, same palette`. Consistency comes from repetition, not memory.

## 9. Size, aspect, quality — what is actually controllable

Two execution paths with different control surfaces (see SKILL.md truth table):

| Lever | Codex Mode A/B (default) | Host-run bundled CLI (`OPENAI_API_KEY`) |
|---|---|---|
| `quality` | not a parameter — accept default | `--quality low\|medium\|high\|auto` |
| exact size | prompt "exactly WxH" → agent downscales after generation | `--size WxH` within constraints |
| `background` transparency | chroma-key + local removal | `gpt-image-1.5 --background transparent` only |
| `input_fidelity` | n/a | edit-only; **not supported for gpt-image-2** (always high) |

**gpt-image-2 size constraints** (deterministic): edges multiples of 16; max edge 3840; long:short ratio ≤ 3:1; **total pixels 655,360–8,294,400**; above 2560×1440 is experimental. A 256×256 icon request is below the pixel floor — that's why it comes back ~1254×1254, not because size adherence is "loose". Generate valid (e.g. 1024×1024) and downscale.

Recommended sizes by use case:
- **App icon**: generate 1024×1024, downscale to target
- **OG / social card**: 1200×630 (630 is not a multiple of 16 — generate 1216×640 and crop, or let the agent handle it via "exactly 1200x630")
- **Blog header**: 1600×900 (same note — agent resizes)
- **Mobile portrait**: 1024×1536 · **Square**: 1024×1024 · **2K**: 2048×2048 / 2048×1152 · **4K**: 3840×2160
- **Format**: PNG default; JPEG for photos (smaller/faster); WebP supported

Quality guidance (CLI path): `low` for drafts and thumbnails; `medium`/`high`/`auto` for final assets, dense text, diagrams, identity-sensitive edits, high-resolution outputs. For production volume, "low + dedicated upscaler" is often cheaper and more reliable than native high-res.

## 10. Anti-patterns

| Anti-pattern | Why it fails | Use instead |
|---|---|---|
| `stunning, masterpiece, cinematic, 8K, ultra-realistic` | Empty adjectives — nothing concrete to render | `overcast daylight, brushed aluminum, 50mm feel, visible surface wear` |
| `modern clean SaaS illustration` | Delegates art direction to generic defaults | `flat editorial vector, off-white background, charcoal linework, one coral accent, asymmetric left-heavy composition` |
| `premium hero background, abstract, gradient` | Produces AI filler that looks cheap in real UI | A real visual: product photo, material texture, editorial illustration, architectural scene |
| Comma keyword soup (`a cat, cute, soft, fluffy, big eyes`) | Word relationships are lost | Natural sentence with relationships intact |
| Leaving schema slots empty | The Codex agent augments them with its own taste (§1) | Fill every slot; empty = delegated |
| Omitting Constraints/Avoid | Watermarks, stray text, drift | Always ban watermark/extra text; always list preserve set on edits |
| `a person smiling at a desk` | Pose, hands, gaze, skin all default | Crop, framing, gaze, hands, object contact, texture, retouching limits |
| Exact text without typography/layout | Text renders but placement/hierarchy is weak | Quoted copy + "appears exactly once" + font/size/placement/contrast |
| "use quality high" in a built-in-path prompt | Quality is not a built-in parameter — silent no-op | Route via host-run bundled CLI `--quality high` |
| Ten changes in one prompt | Output destabilizes | One change per pass, preserve list restated |
| Pure negation (`not blue`, `no cats`) | Negation is weakly applied | Positive rephrase: `warm orange tones`, `dogs only` |
| "same style as before/reference" | Style is not named, so it drifts | Name the style's parts: palette, forms, edges, texture |

## 11. Multilingual (Korean text)

gpt-image-2 renders Korean well, but it breaks more often than English.

- Double quotes + `EXACT TEXT verbatim` marker
- If you see decomposed jamo: add `Korean text rendered as complete Hangul syllables, no decomposed jamo`
- Typeface hint works: `in a Pretendard-like sans-serif Korean typeface`
- Keep Korean text ≥ 5% of image height — small Hangul breaks first
- Dense Korean labels (menus, infographics) → CLI `--quality high`

## 12. Before/After examples

### Example 1 — icon

**Bad**: `make an icon of a seedling, cute, simple`

**Good**: see "Standard generation" recipe in SKILL.md — every schema slot filled, no empty adjectives, valid generation size with exact-size downscale instruction.

### Example 2 — OG image

**Bad**: `make me an OG image for my SaaS, modern and clean`

**Good**: see "OG image (with Korean text)" recipe in SKILL.md — verbatim text blocks with `appears exactly once`, named palette, placement percentages, Hangul guard.

### Example 3 — photo edit

**Bad**: `add a person to this photo`

**Good**:
```
Add a person to the scene: a man in his 40s wearing a charcoal coat, standing on the
sidewalk camera-left at 3m distance, gazing at the building entrance. Preserve
everything else identically: the building facade, all signage and text content, the
parked cars, overcast lighting from camera-right, wet pavement reflections, framing,
camera angle. Match the man's lighting (overcast soft, slight rim from camera-right)
and shadow direction (camera-left, short, consistent with mid-afternoon overcast) to
the existing scene exactly.
```
