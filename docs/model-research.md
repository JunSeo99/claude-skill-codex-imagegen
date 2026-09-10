# GPT Image 2.5 research and implementation decisions

Checked 2026-09-09 against official OpenAI documentation and the installed Codex CLI.

| Model | Official positioning | Implication for our workflow |
|---|---|---|
| [GPT Image 2.5 Flare](https://developers.openai.com/api/docs/models/gpt-image-2.5-flare) | Fast, high-quality everyday generation | Resolve creative direction efficiently and avoid unnecessary revisions. |
| [GPT Image 2.5 Sunburst](https://developers.openai.com/api/docs/models/gpt-image-2.5-sunburst) | Most capable generation/editing, with an emphasis on editing precision | Treat identity, geometry, lettering, and unchanged regions as explicit acceptance criteria. |

The [official prompting guide](https://developers.openai.com/api/docs/guides/image-prompting) describes both models as improving precise edits and subject preservation, and supports transparent backgrounds. It recommends concrete visual requirements, reference roles, and checking retained details across edits. These inform the skill's craft and review instructions. We do not copy the guide into every Claude request.

## What the subscription path actually exposes

On codex-cli 0.153.4, `codex exec --help` identifies `--model` as the agent model. The built-in image tool has no verified selector for these two image models in this launcher. The public [image generation guide](https://developers.openai.com/api/docs/guides/image-generation) documents explicit model selection for API integrations; that does not establish equivalent controls for Codex subscriptions.

Therefore this release has no image API path and no fake `--image-model` flag. Backend identity remains Codex-managed and unreported. Documentation knowledge is distinguished from verified runtime availability. We cannot promise a Flare-to-Sunburst switch during refinement through this transport.

## Decisions for people using Claude Code

- Clear brief: execute immediately, with no mandatory questionnaire.
- An explicit interview: ask a small set of useful questions and wait for answers.
- Multiple directions: generate separate full-size files, then compare locally.
- Editing: attach the selected source and list change/preserve constraints.
- Long generation: detach local workers and continue independent work.
- Token budget: finish all creative reasoning in Claude; forward the short final brief to a light relay, omit skill discovery and generic coding instructions.
- Quota: bound concurrency and repairs; persist completed results instead of regenerating.

These are product/design judgments for this skill, not comparative model benchmarks. Faster does not automatically mean cheaper; subscription limits and image-generation charges to the allowance are controlled by Codex.
