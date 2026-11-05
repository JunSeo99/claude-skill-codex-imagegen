# Execution and model boundaries

## One subscription path

`run_codex_imagegen.py --prompt-file brief.txt` uses the logged-in Codex CLI.
Python standard library only. No image API client, credential forwarding, or billing
fallback. Minimum CLI 0.164.0; verified on 0.164.0 and 0.166.0 (latest stable on
2026-11-05). Runtime/account availability can still vary.

Briefs need no `$imagegen` line; the launcher strips it so Codex does not inject
its own imagegen skill. Options: repeat `--image` for ordered PNG/JPEG/WebP references; `--timeout` defaults
to 300 seconds; `--stats` prints reported relay token usage when available.
`--model` defaults to `gpt-6-luna`; `--reasoning-effort` defaults to `none`. Keep
these defaults unless the account lacks the relay. `image_project.py` forwards the
same `--model`, `--reasoning-effort`, `--timeout`, and
`--allow-default-model-fallback` to every job, including background workers.
An unavailable relay stops. `--allow-default-model-fallback` permits one retry on
the account default, which may consume more subscription allowance. Do not enable
it automatically when the user prioritizes minimal usage. Never pass an image
model ID to `--model`.

The relay's compact instructions replace the general coding instructions for this
one subprocess. The skills catalog is omitted; `config.toml`, project rules, and
unrelated tools are disabled. Codex 0.164.0 still injected the user's global
`~/.codex/AGENTS.md`, so keep secrets out of it. Actual tool schemas and runtime
instructions still consume tokens. A small relay does not make image generation
free or guarantee a specific percentage of token savings.

Prompts travel over stdin in an argument-array subprocess. Generation runs in an
empty temporary directory with read-only sandboxing. PNGs are taken from
`$CODEX_HOME/generated_images/<session id>/` (session id from Codex's own header);
schema-constrained paths inside `generated_images/` are a fallback. The host
copies, exports, and reviews the image. Do not bypass these boundaries on failure.

## Image models (checked 2026-11-05)

OpenAI's API offers GPT Image 2.5 (2026-09-08) and 2.6 (2026-11-04), each as Flare
(speed) and Sunburst (detail, precise edits). OpenAI says Images 2.6 is available
in Codex, but this path cannot select or confirm any of them:

- On 0.164.0–0.166.0 the built-in tool exposes only `prompt`,
  `referenced_image_paths`, `num_last_images_to_include`, `transparent_background`.
- The Codex client sends a fixed `gpt-image-2` label with automatic quality and
  size; the server accepts any label and decides. Its docs naming `gpt-image-2`
  are not evidence of the model that ran.
- Responses carry no model field. C2PA metadata reads only `ChatGPT` / `gpt-image`.
- 2.6 API features (`complexity`, markup edits, SVG, GIF) are not reachable here;
  a GIF request returns a still PNG.

Report the backend as “Codex-managed”. Writing a model name in the brief is not
model selection. If the user requires a pinned model, explain that this
subscription-only skill cannot guarantee it; do not suggest a paid API as the
default solution.

Sources:
- https://openai.com/index/introducing-images-2-6/
- https://developers.openai.com/api/docs/models/gpt-image-2.6-sunburst
- https://developers.openai.com/api/docs/guides/image-prompting

## Export and failure handling

Inspect actual dimensions. 0.153.2 through 0.166.0 (last checked 2026-11-05) returned
≈1.57 MP (e.g. 1672×941, 1254×1254) with approximate prompt aspect ratios; edits kept
the source aspect. Treat this as an observation, not a permanent limit. Keep the
original PNG. Request the closest aspect ratio, then resize proportionally and crop
or pad intentionally with host tools (`sips` on macOS, any installed image tool on
Linux). Never stretch or crop a near-square image into a wide banner. Enlarging a PNG
does not add native detail.

```bash
# 1672×941 original → exact 1600×900 hero (macOS)
sips --resampleWidth 1600 hero.png --out hero-w.png && sips -c 900 1600 hero-w.png --out hero-1600x900.png
```

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
