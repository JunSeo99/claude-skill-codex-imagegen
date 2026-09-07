# gpt-image-2 Prompting Guide

Read this before complex images, images containing text, people, or edit operations. Based on OpenAI's GPT Image prompting guide, the Codex CLI built-in imagegen skill (verified on codex-cli 0.153.2), and direct verification against session logs.

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

Verified in session logs: the brief the launcher sends to `codex exec` is rewritten by the Codex agent before it reaches gpt-image-2. The `revised_prompt` actually sent to the model is a restructured, labeled spec — the agent's own schema — with your details slotted in and constraints tightened.

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

The subscription path does not expose a verbatim/no-rewrite mode. Make constraints explicit and inspect the final image instead of assuming the intermediate prompt is preserved word for word.

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
- Small text, dense labels, infographics, menus, packaging, and multi-font layouts remain fragile. Prefer short labels or overlay production typography in HTML/SVG after generation. Prose such as "use quality high" is not a launcher control.
- If the first result is almost right, iterate with only text/layout corrections; do not rewrite the whole art direction.

## 6. People and photorealism

Write a real photo brief, not a subject label.

- Use the word `photorealistic` directly to engage realism mode.
- Specify crop and body geometry: `full body visible, feet included` / `waist-up` / `hands naturally gripping the handlebars`.
- Specify gaze and action: `looking down at the open book, not at camera`.
- Demand real texture and imperfections: pores, wrinkles, flyaway hair, worn fabric, uneven daylight.
- Block glamor defaults: `honest and unposed, no heavy retouching, no plastic skin, no extra fingers`.
- Close-up portraits and identity-sensitive edits benefit from an attached anchor image and repeated identity invariants.

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
- `--image` order is meaningful and must match the index labels in the prompt. Masks are not exposed on this path; describe the edit region in words instead.
- Edits of a transparent cutout come back opaque (verified on 0.153.2); regenerate transparent assets from an updated brief rather than editing them.
- **Style transfer**: don't say "same style as the reference" — name the style's visual parts (`chunky pixel forms, limited arcade palette, clean silhouette edges`).
- **Character consistency across a set**: the first accepted image is the anchor. Attach it (`Image 1: character reference — keep identity exactly`) and repeat the identity details verbatim in every prompt: `same face, same green hooded tunic, same proportions, same palette`. Consistency comes from repetition, not memory.

## 9. Size, aspect, quality — what is actually controllable

The sandboxed subscription path intentionally exposes a small control surface (see SKILL.md truth table):

| Lever | Behavior |
|---|---|
| `quality` | not a launcher parameter — describe the intended finish and visually verify |
| exact size | not controllable — the built-in tool renders ≈1.57 MP at the brief's aspect ratio; state the aspect ratio, then resize in the host context |
| transparent background | request genuine alpha, then run `verify_png_alpha.py` |
| `input_fidelity` | not a launcher parameter — attach a role-labeled anchor image and repeat invariants |

**Built-in output size is fixed area, not requested pixels.** The tool renders every image at ≈1.57 megapixels and reads only the aspect ratio from the brief (verified on 0.153.2 across 393 outputs: 1:1 → 1254×1254, 3:2 → 1536×1024, 16:9 → 1672×941, 1.91:1 → 1730×909, 3:1 → 2048×768). "256×256" and "1024×1024" both come back as 1254×1254 — that is not loose size adherence, it is the only square size this path produces. The Images API constraints (multiples of 16, 655,360-pixel floor) apply to the API `size` parameter, not to this path.

Write the aspect ratio in `Asset type`, then resize on the host:
- **App icon / favicon**: "1:1 square" → 1254×1254 → `sips -z 512 512`
- **OG / social card**: "1.91:1 landscape OG card" → ~1730×909 → `sips -z 630 1200`
- **Blog header / hero**: "16:9 landscape" → 1672×941 → `sips -z 900 1600`
- **Mobile portrait**: "2:3 portrait" or "9:16 portrait" → 1024×1536 or 941×1672
- **Wide banner**: "3:1" → 2048×768; wider ratios have not been observed — crop on the host
- **Format**: the tool returns PNG; convert to JPEG/WebP on the host if needed

For final assets, inspect the generated pixels and iterate with one targeted change; resize only after acceptance.

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
| "use quality high" in a built-in-path prompt | Quality is not a launcher parameter — silent no-op | Specify concrete finish, materials, lighting, and edge requirements; visually verify |
| Ten changes in one prompt | Output destabilizes | One change per pass, preserve list restated |
| Pure negation (`not blue`, `no cats`) | Negation is weakly applied | Positive rephrase: `warm orange tones`, `dogs only` |
| "same style as before/reference" | Style is not named, so it drifts | Name the style's parts: palette, forms, edges, texture |

## 11. Multilingual (Korean text)

gpt-image-2 renders Korean well, but it breaks more often than English.

- Double quotes + `EXACT TEXT verbatim` marker
- If you see decomposed jamo: add `Korean text rendered as complete Hangul syllables, no decomposed jamo`
- Typeface hint works: `in a Pretendard-like sans-serif Korean typeface`
- Keep Korean text ≥ 5% of image height — small Hangul breaks first
- Dense Korean labels (menus, infographics) → keep labels short, or overlay production typography in HTML/SVG after generation (no quality control is exposed on this path)

## 12. Before/After examples

### Example 1 — icon

**Bad**: `make an icon of a seedling, cute, simple`

**Good**: every schema slot filled, no empty adjectives, "1:1 square" stated in `Asset type`, exact-size downscale performed on the host after acceptance.

### Example 2 — OG image

**Bad**: `make me an OG image for my SaaS, modern and clean`

**Good**: "1.91:1 landscape OG card" in `Asset type`, verbatim text blocks with `appears exactly once`, named palette, placement percentages, Hangul guard, then `sips -z 630 1200` on the host.

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
