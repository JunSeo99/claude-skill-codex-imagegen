# Validation — v0.3.0

Recorded 2026-09-09 on macOS with codex-cli 0.153.4. No separately billed image
API was used. Image backend identity is not reported by this subscription path.

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
cache misses can reach 37,000. The image generation itself is charged separately.

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

## Live generation and editing (0.153.4)

| Artifact | Input | Result |
|---|---|---|
| [Studio photograph](../assets/demo/a-studio.png) | [a.txt](../tests/prompts/demo/a.txt) | 1448×1086 PNG; subject, warm light, limestone and negative space visually checked |
| [Paper direction](../assets/demo/b-paper.png) | [b.txt](../tests/prompts/demo/b.txt) | 1448×1086 PNG; distinct paper medium and graphic composition visually checked |
| [Green edit](../assets/demo/a-studio-v2.png) | Studio image + [edit.txt](../tests/prompts/demo/edit.txt) | 1448×1086 PNG; green glaze applied, overall framing/background retained |

The green edit is a visual preservation example, not a pixel-identity guarantee.
Glaze highlights and texture changed slightly. Images are committed at returned
resolution, without post-generation retouching. The examples do not establish
performance differences between Flare and Sunburst.

The paper direction and green edit ran together using the actual detached worker
with two slots. The launch command returned a job handle while the worker continued;
other repository edits proceeded before generation finished. Both outputs were
saved within approximately **72 seconds** of the worker entering its running state.
One measured batch is not a latency guarantee.

An initial standalone studio attempt generated an image but its final result did
not pass the launcher's structured-path validation. It was rejected rather than
copied. A manually inspected development retry passed. Thus development included
four live image calls, with three accepted artifacts. No automatic failure loop was
used; the rejected result is not included as a successful example.

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

- Codex manages the image model; this launcher cannot pin Flare or Sunburst.
- Jobs run on the local machine and do not survive shutdown or all host process
  cleanup policies. There is no external queue or push-notification service.
- Parallelism shortens waiting when the account allows it; it does not reduce tokens
  per image. Active requests finish after another candidate fails; queued work stops.
- Timeouts and ambiguous completion require inspection before a manual resume.
- The instruction override is scoped to the restricted image relay. It is not a
  recommendation for general coding tasks. Codex may change internal behavior later.
