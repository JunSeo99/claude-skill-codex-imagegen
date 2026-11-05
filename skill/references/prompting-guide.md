# Craft notes — read only the relevant section

The brief order (use → subject → look → composition → constraints) mirrors OpenAI's
advice: state the intended use first, then scene and subject, details, constraints.
Use short labeled lines rather than one long paragraph; there is no magic syntax.

## Art direction (read before any styled or illustrated image)

Naming a style ("soft 3D", "flat illustration") alone yields a generic image.
Decide these first and write them into Look and Composition. A project style
source (`DESIGN.md`, tokens, an existing asset) overrides these defaults.

- Value contrast: the subject must separate from the background by lightness,
  not only hue. Put a light subject on a deep or saturated field, or a dark one on
  a light field; avoid cream on cream and gray on gray.
- Palette roles: one dominant color, one supporting, one accent used in a single
  place where the eye should land. Give hex values. Prefer a specific palette to
  default blue/orange or pastel gradients.
- One focal subject: a single large shape (about half the frame or more) beats
  many small objects. Cut props that do not carry the idea.
- Idea over literal: compress the message into one moment or metaphor ("the one
  card you need, pulled up") instead of illustrating every word.
- Material and light: name the medium's real traits (paper tooth, risograph
  grain, matte render), one key light direction, and grounded contact shadows.
- Cut clichés unless requested: motion lines, sparkles, floating confetti,
  swooshes, generic mascots, and lavender-blue gradients read as stock imagery.

For directions, vary the palette and value structure, not only the medium.

## Text and posters

Quote the final copy, including punctuation and line breaks, and give each string's
position and typography (weight, size, color). Spell unusual names letter by letter.
Ask for no additional text, then inspect spelling and legibility; for Hangul inspect
complete syllables and spacing. Never invent product claims, prices, or a slogan
just to fill the design. For a web hero, prefer real page typography over baked-in
paragraphs. If lettering is still wrong after one correction, disclose it and offer
a deterministic HTML/SVG text overlay. Do not silently remove requested text.

## Product photography

Say "photorealistic" or "real photograph" when that is the goal. Describe surfaces
(brushed metal, translucent glass, matte ceramic), the light source and direction,
viewing angle, contact shadows, and scale; prefer concrete scale, atmosphere, and
color to mood words. Camera specs are appearance cues, not physics. Use a product
reference for packaging or exact geometry. Inspect labels, openings, handles,
reflections, and contact with the ground.

## People

Choose documentary, studio, or editorial intent; specify crop, action, gaze, and
object contact. Natural skin texture and plausible light give the reviewer concrete
acceptance criteria. Check hands, teeth, limbs, and interactions. Attach an identity
anchor for preservation; avoid claiming exact identity fidelity.

## Hero art, icons, and UI assets

Compose a hero around the page's actual text area and keep the subject out of
mobile crop hazards. For icons and in-app assets (settings, like, empty states),
read the project's style source first (`DESIGN.md`, tokens, an existing asset) and
carry its palette, material, corner rounding, and light direction into the brief.
Favor a strong, simple silhouette that reads at the display size; avoid fine detail
and gradients unless the style needs them. Request generous, even padding. Small
state glyphs that change color or need pixel alignment (check, close, chevrons) are
better drawn in code. If an accent color may change later, keep it out of the image
or plan to regenerate. A PNG logo concept is not an editable vector or a brand
identity. Check every icon at its real size on the app's light and dark backgrounds.

## Consistent sets

Settle the style on one representative sample first (offer distinct directions if
none exists). Then write a short style lock and repeat it verbatim in every brief,
after the item-specific line; attach the accepted sample as a style reference.

```text
Asset: in-app icon for a notes app; square 1:1; one image
Image 1: style reference only; match its material, palette, and light
Request: a rounded bell; a small notification dot is the accent detail
Style lock: soft matte 3D; paper-white forms, ink navy (#1F2A44) parts,
signal yellow (#FFC93C) on exactly one small detail; top-left key light;
rounded edges; a bold silhouette that reads at 28 px
Constraints: centered with even padding; transparent background; no floor,
shadow, text, or backdrop
```

Keep each item's request distinct. Hex codes and stroke widths are guides, not
guarantees; compare results side by side and regenerate the outlier, not the set.

## Diagrams

Have Claude establish correct labels and relationships before generation. List
required components and what must not appear. Inspect arrows and factual content
separately from appearance.

## Review once, fix deliberately

Judge against the user's purpose rather than an invented numeric “quality score.”
Fix the highest-impact defect with one local instruction. Reattach the accepted
base and restate what must stay; do not turn a color correction into a new
composition. Keep successes. Model boundaries are in cli-reference.md.
