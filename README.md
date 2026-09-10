<div align="center">

# Codex Imagegen

### Beautiful images. Right inside Claude Code.

Describe it. Compare directions. Refine your favorite. **Keep coding while images render.**

[![skills.sh](https://skills.sh/b/JunSeo99/claude-skill-codex-imagegen)](https://skills.sh/JunSeo99/claude-skill-codex-imagegen/codex-imagegen) [![CI](https://github.com/JunSeo99/claude-skill-codex-imagegen/actions/workflows/ci.yml/badge.svg)](https://github.com/JunSeo99/claude-skill-codex-imagegen/actions) [![MIT](https://img.shields.io/badge/license-MIT-2f6650)](LICENSE)

**English** · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

A Claude Code skill for turning a rough idea into reviewed image files using your **existing Codex subscription**. No image API key. No separate API bill. No new prompt language to learn.

```bash
npx skills add https://github.com/JunSeo99/claude-skill-codex-imagegen --skill codex-imagegen
```

> “Give me two visual directions for a coffee brand. Keep building the page while they generate.”

| 01 · Studio photograph | 02 · Paper illustration | 01, refined · Green glaze |
|:---:|:---:|:---:|
| ![Terracotta cup photographed on limestone](assets/demo/a-studio.png) | ![Terracotta cup as a tactile paper illustration](assets/demo/b-paper.png) | ![Chosen photograph edited to a green cup](assets/demo/a-studio-v2.png) |
| Warm light. Natural material. | Graphic shape. Paper texture. | “Keep the shot. Change only the cup color.” |

Actual outputs through the bundled Codex launcher, not hand-built mockups. [Prompts and verification](docs/validation.md). The image backend is managed by Codex; these examples are not labeled as a particular GPT Image model.

[Get started](#get-started) · [What you can ask](#what-you-can-ask) · [Background generation](#background-generation) · [How it stays lean](#how-it-stays-lean) · [Model support](#gpt-image-25-and-model-support)

## What you can ask

| You say | The skill does |
|---|---|
| “Make a hero image for this page.” | Uses the page's style and layout; creates one image. |
| “I'm not sure what I want. Interview me.” | Asks a few useful questions before spending generation quota. |
| “Show me three different directions.” | Makes separate images and a local comparison gallery. |
| “Use option 2. Change only the background.” | Edits the chosen image, preserves the original, checks for drift. |
| “Make a transparent product cutout.” | Requests genuine alpha and checks decoded PNG pixels. |
| “Make the rest of the assets match this one.” | Reuses the accepted reference and a concise style lock. |
| “Generate these while you finish the UI.” | Starts background workers; Claude continues independent work. |

No mandatory interview for a clear request. No extra variations when you asked for one. No automatic polishing loop after an image already works.

## Get started

You need **Claude Code**, **Python 3.9+**, and **Codex CLI 0.153.4+** on macOS or Linux, with an active Codex login.

```bash
# If Codex is not installed yet:
npm install -g @openai/codex
codex login

# Install this skill:
npx skills add https://github.com/JunSeo99/claude-skill-codex-imagegen --skill codex-imagegen
```

Open a new Claude Code session and ask:

> “Create a warm editorial hero image for this landing page. Leave room for the headline on the left. Save the final image to assets/hero.png.”

Already have a design system? Point Claude at your `DESIGN.md` or attach a reference image. Ask in English, Korean, Japanese, or your preferred language.

<details>
<summary>Manual installation and updates</summary>

Clone the repository and copy the skill into `~/.claude/skills/codex-imagegen/`, or symlink `skill/` there for development. The installable folder is **skill/**, not the repository root.

A reproducible [codex-imagegen.skill](dist/codex-imagegen.skill) archive is also available; unzip it into `~/.claude/skills/`.

To update a Skills CLI installation, run `npx skills update`. For a development clone, pull the latest release. Restart Claude Code if it still shows the previous instructions.

</details>

## Background generation

Image calls themselves wait for Codex. **The host no longer has to.** A detached Python worker owns that wait, while Claude gets a job handle immediately. Multiple candidates run with bounded concurrency: two at a time by default, up to four.

```text
Claude: understand → write brief → start job ───→ continue coding → inspect results
                                     ├─ image A ─┐
                                     └─ image B ─┴─→ PNGs + gallery + manifest
```

Claude normally handles the commands. For scripting:

```bash
python3 skill/scripts/image_project.py \
  --prompt-file brief.txt --out-dir output/hero-v1 --background

python3 skill/scripts/image_project.py --out-dir output/hero-v1 --status
```

For multiple directions, supply a [small JSON plan](tests/prompts/demo/plan.json) with `--plan` and optionally `--workers 2`. Each brief starts with `$imagegen`. Use `--dry-run` to validate without generating.

Outputs include separate PNGs, `index.html`, `manifest.json`, and `worker.log`. Successful candidates survive failures. After inspecting the error, `--resume` verifies and skips completed images. It never restarts the whole set automatically. Keep the machine awake; background jobs are local processes, not cloud queues. Hosts that terminate detached processes may require their own background-task facility.

## How it stays lean

**Claude makes the decisions. Codex receives the finished brief.**

- A compact skill entrypoint loads only the reference needed for the current task.
- The relay uses `gpt-5.6-luna` with reasoning `none` by default.
- General coding instructions are replaced by a short image-only relay instruction. The skills catalog and unrelated capabilities are disabled for that subprocess.
- Interviews, art direction, quality review, galleries, and status checks do not start another Codex conversation.
- A rejected relay does not silently upgrade to a heavier model. Completed images are not regenerated on resume.

A local prompt-input check reduced **automatically injected context from 11,133 to 821 characters**. This is a context measurement, not a claim of 93% lower total tokens or cost. Image/tool tokens and runtime instructions still apply. [Measurement details](docs/validation.md).

## GPT Image 2.5 and model support

[Flare](https://developers.openai.com/api/docs/models/gpt-image-2.5-flare) is positioned for fast everyday generation. [Sunburst](https://developers.openai.com/api/docs/models/gpt-image-2.5-sunburst) targets demanding quality and precise edits. The skill's prompting and review guidance incorporates the new [official image guidance](https://developers.openai.com/api/docs/guides/image-generation).

**This subscription path cannot currently pin Flare or Sunburst.** Codex manages the built-in image backend. `--model` chooses the lightweight text relay, not the image model. A [direct CLI probe](docs/model-capability-probe.json) also reported no image-model parameter; whether natural-language model names influence routing remains unknown. We do not substitute a separately billed API, invent a model selector, or label an unverified output as GPT Image 2.5. [Research and capability boundaries](docs/model-research.md).

## Quality you can inspect

Generation is only one step. Claude inspects composition, exact text, product geometry, unwanted changes, and edges before delivery. Transparent cutouts must pass the bundled pixel validator:

```bash
python3 skill/scripts/verify_png_alpha.py --require-transparent-corners image.png
```

Keep original files. Export proportionally to the requested size; no stretching and no “native 4K” claim for an upscale. Generative edits can drift, text can need correction, and account limits still apply. The older 0.153.2 size/alpha observations are retained as dated evidence, not universal model limits.

The Codex child uses a read-only sandbox, isolated configuration, an environment allowlist, and validated output paths. Background workers only orchestrate this same launcher. [Security](SECURITY.md).

## Built for reuse

The skill follows the folder-based Agent Skills format with a concise intent description, relative references, and Python-standard-library scripts. The README is for people; runtime instructions live in [skill/SKILL.md](skill/SKILL.md).

| Resource | Purpose |
|---|---|
| [Skill entrypoint](skill/SKILL.md) | Intent routing and the minimal generation workflow |
| [Creative directions](skill/references/directions.md) | Separate candidates, selection, and resumable jobs |
| [Editing guide](skill/references/editing.md) | Reference roles, preservation, transparent edits |
| [CLI reference](skill/references/cli-reference.md) | Options, capability boundaries, troubleshooting |
| [Changelog](CHANGELOG.md) | Versioned behavior changes |
| [Validation](docs/validation.md) | Tests, live observations, and limitations |

## Contribute a result

Found a prompt that works especially well, or an edit that drifts? Open an issue with the prompt, expected result, CLI version, and an image you have permission to share. Remove private material first. Contributions that improve reproducible image quality are welcome.

If this earns a place in your Claude Code workflow, **star the repository** to find it again and follow releases.

[MIT license](LICENSE). Independent project; not affiliated with Anthropic or OpenAI.
