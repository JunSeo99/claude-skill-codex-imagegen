# gpt-image-2 Prompting Guide

Read this before complex images, images containing text, or edit operations. Content based on fal.ai, OpenAI Cookbook, and direct verification.

## Table of contents

1. Five-part prompt structure
2. The first-50-words rule
3. Text rendering
4. Editing (change-X / preserve-Y pattern)
5. Size, aspect, quality
6. Anti-patterns
7. Multilingual (non-Latin scripts)
8. Before/After examples

---

## 1. Five-part prompt structure

Assemble every prompt in this order. Missing slots get filled in by the model's guesses, which produces inconsistent results.

| Slot | What goes here | Example |
|---|---|---|
| **1. Scene/context** | Environment, time, mood, camera viewpoint | "A quiet classical museum gallery in soft afternoon light" |
| **2. Subject** | The main figure or object | "A woman in her 30s standing in front of a large oil painting" |
| **3. Details** | Style, medium, lighting direction, lens, color, texture | "Natural smile, realistic skin texture, beige knit sweater, 50mm feel, eye-level full-body framing, marble floor reflections" |
| **4. Use case** | Purpose — drives size and aspect ratio | "Editorial photo, 4:3 aspect, 1536x1152 PNG" |
| **5. Constraints** | What to preserve and what to forbid | "No watermark, no extra text, no border, preserve identity across iterations" |

> "The fifth slot is where most mediocre prompts fail silently." — fal.ai

When slot 5 is empty, watermarks, logos, and stray text show up often.

## 2. The first-50-words rule

> "The model gives more weight to the first 50 words of your prompt."

- **Front**: style, subject, mood (the most important elements)
- **Back**: background objects, color accents, secondary detail

Word order changes the result. The same vocabulary, placed earlier, is reflected more strongly.

## 3. Text rendering

gpt-image-2 has strong text rendering (>99% accuracy) but still rewards careful specification.

**Rules**:
- Wrap literal strings in **double quotes** or **ALL CAPS**: `headline reads "Notable"`
- Add `EXACT TEXT verbatim` or `verbatim` marker
- State typography: weight, size relative to image, placement (top-left/center/etc.)
- For tricky words (brand names, proper nouns), spell **letter-by-letter**: `the word "Notable" (N-o-t-a-b-l-e)`
- **Always include**: `no extra text, no duplicate text, no captions, no labels unless specified`
- For small text or dense layouts, use `quality="medium"` or `"high"`

**Example — OG image text**:

```
Headline (EXACT TEXT verbatim): "Notable"
Subheadline (EXACT TEXT verbatim): "fast notes for fast minds"
Bold sans-serif, headline ~80px equivalent, subheadline ~32px, left-aligned,
top-left positioning at 8% padding. No extra text anywhere.
```

## 4. Editing (change-X / preserve-Y pattern)

This is the most common failure mode when attaching a reference image with `-i <file>`.

**Rules**:
1. **Narrow the change to a single target**: "change only the background color"
2. **List the preserve set explicitly**: "preserve: face, pose, lighting direction, framing, all text content, geometry, background objects"
3. **Repeat — to fight drift**: rewrite the same preserve list every iteration
4. **One change per pass**: "make lighting warmer" → confirm → "remove extra tree"

**Bad**:
```
Make this better and more professional looking
```

**Good**:
```
Change only the sky from overcast to clear blue with soft cumulus clouds.
Preserve everything else identically: the woman's face, pose, beige sweater,
the painting on the wall, marble floor, lighting on her skin (still soft
afternoon side-light from camera-left), camera angle, framing, all texture
detail. Match cloud lighting to existing skin lighting direction.
```

## 5. Size, aspect, quality

Per the [OpenAI image-generation guide](https://developers.openai.com/api/docs/guides/image-generation):

| Parameter | Value | Note |
|---|---|---|
| Size | Multiples of 16; max edge ≤ 3840 px; long:short ratio ≤ 3:1; total pixels between 655,360 and 8,294,400; or `auto` | gpt-image-2 may still not return exactly the requested pixels — host resizes with `sips` (macOS) / `convert` (Linux) |
| Quality | `low` / `medium` / `high` / `auto` (default) | Use `medium`+ for small text or dense designs |
| Format | PNG (default), JPEG (faster, smaller), WebP | Photos → JPEG. Line art / icons → PNG |
| Background | opaque (default) | gpt-image-2 does NOT support `background: "transparent"` (quoted from the OpenAI guide). For transparency, fall back to gpt-image-1.5 via the Image API |

Recommended **final** output sizes by use case (these are post-`sips` host-resize targets, not API request sizes). For any target smaller than the API minimum of 655,360 pixels (≈ 810×810), request a larger size from gpt-image-2 and resize down on the host:

- **App icon**: 512×512, 1024×1024 PNG (request 1024×1024 from the model; resize down to 512×512 on the host if needed)
- **OG / social card**: 1200×630 PNG — Facebook/Twitter standard (request `1536×1024` or similar, then resize)
- **Blog header**: 1600×900 PNG
- **Mobile portrait illustration**: 1024×1536 PNG
- **Square illustration**: 1024×1024 PNG

## 6. Anti-patterns

| Anti-pattern | Why it fails | Use instead |
|---|---|---|
| `stunning, masterpiece, cinematic, 8K, ultra-realistic, beautiful` | Empty adjectives — the model can't interpret them concretely | Concrete details: `overcast daylight, brushed aluminum, 50mm feel, visible surface wear` |
| Comma-separated keyword soup (`a cat, cute, soft, fluffy, big eyes, pink ribbon`) | The relationships between words are lost | Natural sentence: `A fluffy gray kitten with big eyes wearing a pink ribbon, sitting on a wooden table in soft window light` |
| Omitting the preserve slot | Edits drift; watermarks appear | Always include slot 5: "no watermark, no extra text", plus preserve list when editing |
| Ten changes in one prompt | Output becomes unstable | Iterate one change at a time, repeating the preserve list each pass |
| Pure negative instructions only (`not blue`, `no cats`) | Negation is weakly applied | Rephrase positively: `warm orange tones`, `dogs only` |

## 7. Multilingual (non-Latin scripts)

gpt-image-2 improved multilingual text rendering, but non-Latin scripts (CJK, Arabic, Devanagari, etc.) still break more often than English.

**Tips**:
- Use double quotes + EXACT TEXT verbatim marker
- If glyphs decompose (e.g. Hangul jamo splitting apart, Arabic letters not joining), explicitly demand correct shaping: "rendered as properly shaped script glyphs, no decomposed characters"
- You can hint a typeface: "in a humanist sans-serif typeface designed for this script"
- Small non-Latin text breaks easily — keep it ≥5% of image height

## 8. Before/After examples

### Example 1 — Generic icon

**Bad**:
```
make an icon of a seedling, cute, simple
```

**Good**:
```
A minimalist line-art icon, 256x256 PNG, depicting a single seedling with
two leaves growing from a flat horizon. Style: clean monochrome vector,
single black stroke (2px) on pure white background, centered composition,
generous padding. Use case: app icon for an indie note-taking app.
No text, no shadows, no gradients, no watermark, no border.
Save to ./assets/icon.png at exactly 256x256 pixels.
```

### Example 2 — OG image

**Bad**:
```
make me an OG image for my SaaS, modern and clean
```

**Good**:
```
Open Graph card, 1200x630 PNG, for a note-taking app called "Notable".
Left half: bold sans-serif headline "Notable" (EXACT TEXT verbatim) at
~80px equivalent, dark navy (#0A1F3D) on white, top-left at 8% padding.
Below it, subhead "fast notes for fast minds" (EXACT TEXT verbatim)
at ~32px in medium gray.
Right half: soft radial gradient from pale blue (#E8F2FF) to white, with
a faint 80%-opacity line-art seedling silhouette near the center-right.
No extra text anywhere, no duplicate text, no logo, no watermark.
```

### Example 3 — Photo edit

**Bad**:
```
add a person to this photo
```

**Good**:
```
Add a person to the scene: a man in his 40s wearing a charcoal coat,
standing on the sidewalk camera-left at 3m distance from the camera,
gazing at the building entrance. Preserve everything else identically:
the building facade, all signage and text content, the parked cars,
overcast lighting from camera-right, wet pavement reflections, framing,
camera angle. Match the man's lighting (overcast soft, slight rim from
camera-right) and shadow direction (camera-left, short shadow consistent
with mid-afternoon overcast) to the existing scene exactly.
```
