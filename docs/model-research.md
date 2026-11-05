# Image model research and implementation decisions

First checked 2026-09-09 (GPT Image 2.5); re-checked 2026-11-05 after Images 2.6.
See the re-check section below for the current state.

| Model | Official positioning | Implication for our workflow |
|---|---|---|
| [GPT Image 2.5 Flare](https://developers.openai.com/api/docs/models/gpt-image-2.5-flare) | Fast, high-quality everyday generation | Resolve creative direction efficiently and avoid unnecessary revisions. |
| [GPT Image 2.5 Sunburst](https://developers.openai.com/api/docs/models/gpt-image-2.5-sunburst) | Most capable generation/editing, with an emphasis on editing precision | Treat identity, geometry, lettering, and unchanged regions as explicit acceptance criteria. |

The [official prompting guide](https://developers.openai.com/api/docs/guides/image-prompting) describes both models as improving precise edits and subject preservation, and supports transparent backgrounds. It recommends concrete visual requirements, reference roles, and checking retained details across edits. These inform the skill's craft and review instructions. We do not copy the guide into every Claude request.

## What the subscription path actually exposes

On codex-cli 0.153.4, `codex exec --help` identifies `--model` as the agent model. The built-in image tool has no verified selector for these two image models in this launcher. The public [image generation guide](https://developers.openai.com/api/docs/guides/image-generation) documents explicit model selection for API integrations; that does not establish equivalent controls for Codex subscriptions.

Therefore this release has no image API path and no fake `--image-model` flag. Backend identity remains Codex-managed and unreported. Documentation knowledge is distinguished from verified runtime availability. We cannot promise a Flare-to-Sunburst switch during refinement through this transport.

### Direct Codex response — 2026-09-10

We also asked the actual subscription CLI, using the same lightweight relay and
tool isolation as the launcher, to report its currently visible image-tool
parameters without generating an image. This checks the agent-facing interface,
rather than assuming the CLI help lists every tool argument.

Codex reported `image_gen__imagegen` with these three parameters:

| Parameter | Reported type |
|---|---|
| `prompt` | Required string |
| `referenced_image_paths` | Optional nullable array of strings |
| `num_last_images_to_include` | Optional nullable integer |

It reported `supported_by_parameter: false` for both `gpt-image-2.5-flare` and
`gpt-image-2.5-sunburst`. For natural-language selection, its exact response was:

> Unknown; the visible tool description does not say that a natural-language model-name instruction selects the backend.

The [full request and response](model-capability-probe.json) records CLI 0.153.4,
Luna with reasoning `none`, and 2,810 reported tokens. This is Codex's account-local
report of its exposed interface; it does not establish undocumented server routing
behavior or future versions. We therefore keep the existing subscription-only
implementation and do not add an inert model-selection flag. If a future probe
exposes a real selector, use its exact parameter and accepted values. Do not run a
capability interview before every image; check only when explicitly needed.

### Re-check on codex-cli 0.164.0 — 2026-10-25

The same probe on 0.164.0 (`gpt-6-luna`, reasoning `none`) reported a fourth tool
parameter, `transparent_background: boolean|null`. There is still no image-model
parameter. The relay instructions now ask for `transparent_background=true` when the
brief requests a transparent background.

## Decisions for people using Claude Code

- Clear brief: execute immediately, with no mandatory questionnaire.
- An explicit interview: ask a small set of useful questions and wait for answers.
- Multiple directions: generate separate full-size files, then compare locally.
- Editing: attach the selected source and list change/preserve constraints.
- Long generation: detach local workers and continue independent work.
- Token budget: finish all creative reasoning in Claude; forward the short final brief to a light relay, omit skill discovery and generic coding instructions.
- Quota: bound concurrency and repairs; persist completed results instead of regenerating.

These are product/design judgments for this skill, not comparative model benchmarks. Faster does not automatically mean cheaper; subscription limits and image-generation charges to the allowance are controlled by Codex.

### Re-check after Images 2.6 — 2026-11-05

OpenAI released Images 2.6 on 2026-11-04 (API models `gpt-image-2.6-flare` and
`gpt-image-2.6-sunburst`, adding `complexity`, markup edits, SVG, and GIF output to
the Image API) and said it is available in ChatGPT and Codex. On codex-cli 0.166.0
the built-in tool still exposes only the four parameters above. The open-source
client posts a fixed `gpt-image-2` label with automatic quality and size, and
public tests show the Codex images endpoint accepting even a nonexistent model name,
so the server chooses the model. Responses and C2PA metadata do not identify it.
A GIF request returned a still PNG; an alpha client with GIF support received
HTTP 400 from the server. Conclusion unchanged: report the backend as Codex-managed,
never label outputs with a model version, and add no inert model selector.
Sources: [announcement](https://openai.com/index/introducing-images-2-6/),
[2.6 Sunburst](https://developers.openai.com/api/docs/models/gpt-image-2.6-sunburst),
[prompting guide](https://developers.openai.com/api/docs/guides/image-prompting).
