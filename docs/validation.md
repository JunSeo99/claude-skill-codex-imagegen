# Validation — v1.0.0

Recorded on macOS with a ChatGPT-login Codex subscription, newest first; the
original v0.3.0 baseline used codex-cli 0.153.4 (2026-09-09). No separately billed
image API was used. Image backend identity is not reported by this subscription path.

## Re-check after Images 2.6 on codex-cli 0.166.0 (2026-11-05)

OpenAI announced Images 2.6 on 2026-11-04 and said it is available in Codex. On
0.166.0 (still the latest stable CLI) a tool-schema probe with no generation listed
the same four `image_gen.imagegen` parameters and no model, quality, size, or format
control (9,452 tokens). Defaults only (`gpt-6-luna`, reasoning `none`):

| Brief | Time | Result |
|---|---:|---|
| 16:9 product hero (terracotta cup), launcher | 29 s | 1672×941 RGB, 13,124 relay tokens |
| Transparent 1:1 icon (brass compass) | 63 s | 1254×1254 RGBA |
| Cutout edit of a packaged-product photo with dense label text | background job | 1254×1254 RGBA, corners clear, every label word correct; the bag came back larger in the frame |
| Cutout edit of a studio product photo (the retired 0.153.4 demo) | background job | 1448×1086 RGBA, framing and handle hole preserved |
| `tests/prompts/transparent-e2e.txt` (rewritten brief) | background job | 1254×1254 RGBA, `--require-transparent-corners` passed |

Sizes match 0.153.2 and 0.164.0, and timings are not faster, but one sample cannot
identify the backend. Responses carry no model field and the C2PA manifest reads only
`ChatGPT` / `gpt-image`, so outputs are still not labeled with a model. A brief asking
for an animated GIF returned a still PNG. The 0.168.0-alpha.2 client adds a `gif`
option behind `features.image_generation_animation`; with it enabled the server
answered HTTP 400 “GIF output is not enabled for this request.”

The 0.153.4 demo briefs began with `$imagegen`, which the launcher has stripped
since 0.4.0; the current demo briefs do not use it.

## Re-check on codex-cli 0.166.0 (2026-11-02)

The v0.4.0 launcher, defaults only (`gpt-6-luna`, reasoning `none`), ran
`tests/prompts/transparent-e2e.txt` once: 55 s, 8,546 relay tokens, one PNG found
under `generated_images/<session id>/`. Result: 1316×1195 RGBA, all four corners
alpha 0, `verify_png_alpha.py --require-transparent-corners` passed. Subject alpha
was again mostly 250–254; `solidify_png_alpha.py` raised 499,296 pixels to 255 and
the copy still passed. Faint stray specks of the subject color remained outside the
outline in both the original and the solidified copy, so inspect cutouts visually.

## Re-validation on codex-cli 0.164.0 (2026-10-25)

Relay `gpt-6-luna`, reasoning `none`, same isolation flags as the launcher, with the
transparency line in the relay instructions. Two jobs ran in parallel on macOS.

| Brief | Time | Relay tokens | Result |
|---|---:|---:|---|
| 16:9 product hero (terracotta cup) | 22 s | 37,075 | 1672×941 RGB; composition and light match the brief |
| Transparent 1:1 icon cutout (brass compass) | 52 s | 13,083 | 1254×1254 RGBA; 48% fully transparent pixels, all four corners alpha 0; faint colored fringe on the outline |

A tool-schema probe with no image generation reported `image_gen__imagegen` with
`prompt`, `referenced_image_paths`, `num_last_images_to_include` and the new
`transparent_background`. The probe used 9,547 tokens. Relay token counts vary widely
between calls and are well above the 0.153.4 figures below, so treat them as samples.
The rollout explains the size: each model request carried about 10,800 input tokens
(Codex system instructions and tool schemas), and an image run needs at least two
requests (call the tool, then answer). Codex's `tokens used` counts uncached tokens,
so a run with good cache reuse reports about 11,000 and one with extra requests or
cache misses can reach 37,000. The image generation itself draws on the Codex
allowance separately; nothing is billed to an API account.

The rollout also showed what filled those 10,800 tokens: Codex injected its whole
built-in `imagegen` skill (19,274 characters) because the brief began with `$imagegen`,
plus permission and collaboration instructions. The launcher now strips the
`$imagegen` mention and sets `include_permissions_instructions=false` and
`include_collaboration_mode_instructions=false`. A live run afterwards still called
the image tool with `transparent_background: true`, and input per request fell to
about 5,900 tokens (−45%). Codex still adds a multi-agent role note (about 2,400
characters, despite `--disable multi_agent`) and the user's global `AGENTS.md`;
no setting to drop those was found.
The relay often reported an empty or invented path (`""`,
`$CODEX_HOME/generated_images/red_origami_fox.png`) although the image was saved.
A saved session rollout shows why: on 0.164.0 the relay calls the image tool from
Codex's JavaScript `exec` code-mode wrapper and printed only the result's text
parts, which carry no path, so the model never saw where the file went. The rollout
also confirms `transparent_background: true` was passed for a transparent brief. The launcher now
reads the PNGs from `generated_images/<session id>/`, using the `session id:` header
Codex prints, and only falls back to the model-reported paths. A transparent sticker
then passed `verify_png_alpha.py --require-transparent-corners` end to end (44 s,
11,088 relay tokens). In both transparent outputs the subject's alpha was mostly
250–254, not 255, so cutouts are about 1–2% see-through.

`gpt-6-luna` and `gpt-5.6-luna` both accept reasoning `none`, although
`codex debug models` does not list it. `skip_host_skill_discovery` is still an
under-development feature and prints a warning on stderr.

## README demo (codex-cli 0.166.0, 2026-11-05)

Both steps ran as detached background plans with the default relay. Images are
committed downscaled for the README (directions and empty state to 640 px, icons
to 320 px) without retouching.

| Step | Briefs and plan | Result |
|---|---|---|
| Three onboarding directions | [plan.json](../tests/prompts/demo/plan.json): [a-ink](../tests/prompts/demo/a-ink.txt), [b-riso](../tests/prompts/demo/b-riso.txt), [c-papercraft](../tests/prompts/demo/c-papercraft.txt) | 3 × 1254×1254 RGB; distinct palettes and value structures, one focal subject each, no lettering |
| Set in direction A | [set-plan.json](../tests/prompts/demo/set-plan.json): four icons and an empty state, each repeating the same style lock with direction A attached as style reference | 4 icons 1254×1254 RGBA, `--require-transparent-corners` passed; empty state 1254×1254 RGB |

A first attempt with only a named style and cream-on-cream palette produced muddy,
cluttered images; the art-direction section in `prompting-guide.md` came from that
comparison. The set plan's reference points at the committed 640 px copy; the run
itself attached the full-resolution direction image. Visible limits: the search
icon's lens reads as glossier glass than the matte set, and the folder resembles
the tray. A second set in direction C was also generated for comparison and kept
out of the repository.

Earlier demos (codex-cli 0.153.4, 2026-09-09) used a studio photograph, a paper
illustration, and a color edit of the same product; they were retired in 1.0.0.
That run measured about **72 seconds** for two detached jobs in parallel, and one
standalone attempt was rejected by path validation rather than copied.

## Context and token scope

| Measurement | Before | After |
|---|---:|---:|
| Main SKILL.md, whitespace-delimited words | 2,198 | 762 |
| Automatically injected prompt-input text, characters | 11,133 | 821 |
| Bundled skill size | 1,538,759 bytes | approximately 22 KB |

The prompt-input measurement used `codex debug prompt-input` in an empty temporary
directory, with plugins/apps disabled and the same `gpt-5.6-luna` relay. The second
run additionally set `skills.include_instructions=false` and enabled
`skip_host_skill_discovery`. Counts sum text in the emitted input messages.
This does not measure the full request, system instructions, tool schemas, image
tokens, or billed usage. It is not a 93% total-token/cost reduction claim.

The accepted studio call reported 10,428 relay tokens. The two-job batch reported
10,725 and 15,559 tokens; the shared log does not attribute those two numbers to
individual candidates. The image input on an edit can increase usage. The compact
relay still has nonzero runtime/tool overhead. No old/new total-token A/B benchmark
was performed, avoiding extra image generations solely for marketing metrics.

Sample images now live outside the installed skill; the small bundle still contains
all runtime references and scripts. This affects download size, not model quality.

## Automated checks

Run from the repository root:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/package_skill.py --check
```

30 tests cover the Codex status check, alpha solidify, `$imagegen` stripping, alpha decoding, environment isolation, structured-path validation,
disguised/symlink PNG rejection, minimal relay defaults, opt-in relay fallback,
plan preflight, stable input hashes, interrupted batches, verified resume, gallery
escaping, background dispatch, local status, and bounded concurrency.

The detached-process integration test uses a local fake Codex executable: two
delayed calls overlap, the launch returns before either finishes, and the detached
worker writes both results. This test uses no network or subscription quota.
It supplements the real two-job smoke test above.

The standard skill frontmatter validator passed. CI runs the suite and bundle
verification on Python 3.9 and 3.13 under Linux. Live image generation was tested
on macOS; Linux image generation itself was not exercised against an account.

## Transparency baseline

The committed [transparent fixture](../tests/fixtures/transparent-e2e.png) is decoded
on every test run. The older live baseline (0.149.0 and 0.153.2) had real transparent
pixels and clear corners. A 0.153.2 edit returned opaque checkerboard pixels.
No new transparent-model comparison was generated for this release. The skill
validates current output and treats that older failure as a dated observation.

## Known transport boundaries

- Codex picks the image model server-side; this launcher cannot select or identify
  it (GPT Image 2, 2.5, or 2.6; Flare or Sunburst).
- Jobs run on the local machine and do not survive shutdown or all host process
  cleanup policies. There is no external queue or push-notification service.
- Parallelism shortens waiting when the account allows it; it does not reduce tokens
  per image. Active requests finish after another candidate fails; queued work stops.
- Timeouts and ambiguous completion require inspection before a manual resume.
- The instruction override is scoped to the restricted image relay. It is not a
  recommendation for general coding tasks. Codex may change internal behavior later.
