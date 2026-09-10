# Validation — v0.3.0

Recorded 2026-09-09 on macOS with codex-cli 0.153.4. No separately billed image
API was used. Image backend identity is not reported by this subscription path.

## Live generation and editing

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

25 tests cover alpha decoding, environment isolation, structured-path validation,
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
