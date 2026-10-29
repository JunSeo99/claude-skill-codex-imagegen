# Execution and model boundaries

## One subscription path

`run_codex_imagegen.py --prompt-file brief.txt` uses the logged-in Codex CLI.
Python standard library only. No image API client, credential forwarding, or billing
fallback. Minimum/verified CLI: 0.164.0. Runtime/account availability can still vary.

Briefs need no `$imagegen` line; the launcher strips it so Codex does not inject
its own imagegen skill. Options: repeat `--image` for ordered PNG/JPEG/WebP references; `--timeout` defaults
to 300 seconds; `--stats` prints reported relay token usage when available.
`--model` defaults to `gpt-6-luna`; `--reasoning-effort` defaults to `none`.
An unavailable relay stops. `--allow-default-model-fallback` permits one retry on
the account default, which may consume more subscription allowance. Do not enable
it automatically when the user prioritizes minimal usage. Never pass an image
model ID to `--model`.

The relay's compact instructions replace the general coding instructions for this
one subprocess. The skills catalog is omitted; user config, project rules, and
unrelated tools are disabled. Actual tool schemas and runtime instructions still
consume tokens. A small relay does not make image generation free or guarantee a
specific percentage of token savings.

Prompts travel over stdin in an argument-array subprocess. Generation runs in an
empty temporary directory with read-only sandboxing. PNGs are taken from
`$CODEX_HOME/generated_images/<session id>/` (session id from Codex's own header);
schema-constrained paths inside `generated_images/` are a fallback. The host
copies, exports, and reviews the image. Do not bypass these boundaries on failure.

## GPT Image 2.5

Official OpenAI guidance distinguishes Flare (fast everyday generation) from
Sunburst (demanding quality and precise editing). Both accept image references.
Translate that distinction into a workflow: settle direction before spending on
revisions, and carefully inspect preservation on exact edits.

On 0.164.0 the built-in tool exposes `prompt`, `referenced_image_paths`,
`num_last_images_to_include` and `transparent_background`, but still no image-model
selector. Writing a model
name in the brief is not model selection. Report the backend as “Codex-managed”;
do not claim either 2.5 model was used. Quality, native size, and mask API controls
are not launcher flags. If the user requires a pinned model, explain that this
subscription-only skill cannot currently guarantee it. Do not suggest switching
to a paid API as the default solution.

Sources (checked 2026-09-09):
- https://developers.openai.com/api/docs/models/gpt-image-2.5-flare
- https://developers.openai.com/api/docs/models/gpt-image-2.5-sunburst
- https://developers.openai.com/api/docs/guides/image-prompting

## Export and failure handling

Inspect actual dimensions. 0.153.2 and 0.164.0 both returned ≈1.57 MP (e.g. 1672×941, 1254×1254)
with approximate prompt aspect ratios. Do not apply that as a permanent 2.5 limit. Keep the original
PNG. For exact exports, use proportional resize plus intentional crop or padding
with host tools (`sips` on macOS, ImageMagick on Linux). Never stretch a near-square
image into a wide hero. Enlarging a PNG does not add native detail.

| Failure | Response |
|---|---|
| CLI missing | Install/update Codex CLI, then `codex login` directly |
| Login/usage limit | Report the issue/reset time; do not retry or change billing |
| Unsupported relay/effort | Pick an available light relay; do not silently upgrade |
| Invalid generated path | Reject it; do not search unrelated files for substitutes |
| Timeout | Stop and report; it may have generated already, so no automatic repeat |
| Wrong text / alpha / geometry | One targeted correction, then report remaining defect |
| Old CLI rejects controls | Update CLI; do not weaken isolation flags |

Temporary briefs and local galleries may contain private material. Keep them local
unless sharing is requested. Remove confidential temporary briefs after delivery.
