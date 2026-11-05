# Targeted edits without restarting the design

Inspect the source in Claude before composing the edit. Resolve “the second one”
from the current gallery/manifest. If the reference is ambiguous, clarify which
image; never select an unrelated recent file. Pass local images using `--image`.

```text
Asset: revised onboarding illustration; one image; retain source aspect ratio
Image 1: accepted base to edit
Change: only the pulled card's tab color, from signal yellow to coral
Preserve: tray, other cards, layout, framing, material, light direction,
shadows, background and empty space; no added text or objects
```

For multiple references, number them and give each one role: base, identity,
material, clothing, style, or background. Supply the minimum set, in that order.
Say "change only …", state the location and scope, and repeat critical preservation
rules on every pass. Avoid accumulated conversation history and contradictory
requests. When drift appears, start again from the last accepted image, not the
rejected edit, with the drifted detail added to the preserve list; if the retry
still drifts, keep the original and report.

Save an edited sibling (`onboarding-v2.png`) and inspect it beside the original.
Check both the requested change and unexpected changes elsewhere. Report drift;
generative editing does not guarantee unchanged pixels. When pixel-identical
regions are essential, explain the limitation and propose local compositing only
with the user's agreement. Do not claim the launcher supports mask parameters.

## Transparency

Request actual alpha and generous clear padding; forbid painted checkerboards,
matte backgrounds, unwanted floors, and shadows only when unwanted by the user.
Describe only the isolated subject: a described backdrop or scene can win over the
transparency flag. Run `verify_png_alpha.py`; add `--require-transparent-corners`
for isolated cutouts. Inspect hair, fur, glass and fine edges visually after pixel
validation passes. On later edits, repeat that the background stays transparent.

Say "transparent background" explicitly in the brief: since CLI 0.164.0 the built-in
tool exposes a `transparent_background` flag, and the relay sets it when asked.
On 0.166.0 (2026-11-05) generated icons and cutouts of existing photos returned real
RGBA with clear corners, including a bag whose dense label text stayed correct.
Subject alpha was mostly 250–254, not 255; flatten it only if the user needs a fully
solid cutout. A cutout is re-rendered, not masked: compare labels, small text, and
fine detail with the source, and note that framing can change (one bag came back
larger in the frame). Earlier versions showed a faint outline fringe and, on 0.153.2,
an opaque checkerboard, so validate every result.
If alpha is lost, make at most one focused repair; if it still fails, retain the
source and report the defect. When exact pixels matter, say so and suggest a
deterministic cutout tool. Never silently replace an exact edit with a fresh image.
