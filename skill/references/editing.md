# Targeted edits without restarting the design

Inspect the source in Claude before composing the edit. Resolve “the second one”
from the current gallery/manifest. If the reference is ambiguous, clarify which
image; never select an unrelated recent file. Pass local images using `--image`.

```text
Asset: revised product photograph; one image; retain source aspect ratio
Input images: Image 1 is the accepted base
Change: only the cup's glaze from terracotta to muted forest green
Preserve: cup shape and handle, framing, limestone surface, light direction,
contact shadow, background and empty space; no added text or objects
```

For multiple references, say which supplies the base, identity, material, clothing,
or background. Supply the minimum set, in that order. State the location and scope
of the change; repeat critical preservation rules on every pass. Avoid accumulated
conversation history and contradictory requests. Start from the last accepted
image, not a rejected edit, when drift appears.

Save an edited sibling (`a-studio-v2.png`) and inspect it beside the original.
Check both the requested change and unexpected changes elsewhere. Report drift;
generative editing does not guarantee unchanged pixels. When pixel-identical
regions are essential, explain the limitation and propose local compositing only
with the user's agreement. Do not claim the launcher supports mask parameters.

## Transparency

Request actual alpha and generous clear padding; forbid painted checkerboards,
matte backgrounds, unwanted floors, and shadows only when unwanted by the user.
Run `verify_png_alpha.py`; add `--require-transparent-corners` for isolated cutouts.
Inspect hair, fur, glass and fine edges visually after pixel validation passes.

Say "transparent background" explicitly in the brief: since CLI 0.164.0 the built-in
tool exposes a `transparent_background` flag, and the relay sets it when asked.
A 0.164.0 cutout came back as real RGBA with clear corners but a faint colored fringe
along the outline, so check edges closely. Subject alpha was mostly 250–254, not 255;
flatten it to opaque only if the user needs a fully solid cutout. An older 0.153.2 transparent edit returned
an opaque checkerboard; re-validate edits rather than assuming either outcome.
Try the requested edit and validate it. If alpha is lost, make at most one focused
repair; if it still fails, retain the source and report the defect. Offer regeneration
as a new alternative only if identity/layout loss is acceptable. Never silently
replace an exact edit with a fresh image.
