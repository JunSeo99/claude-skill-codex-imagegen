# Security

## Reporting a vulnerability

Open a GitHub issue or email jun@indexfinger.org.

## Trust boundary

This skill runs the OpenAI Codex CLI as a sub-agent from inside your Claude Code session. The Codex sub-agent is itself an LLM that decides which shell commands to execute on your machine. Whatever permissions you grant the Codex sub-agent, you are granting to a model whose prompt you do not fully control once generation begins.

## The two run modes

This skill defines two run modes. Read SKILL.md for the full workflow; this file documents the security difference.

### Mode A — Safe default

Invocation:

```bash
codex exec --sandbox workspace-write '$imagegen <PROMPT>. Generate the image
and print ONLY the absolute path of the resulting PNG. Do NOT copy or move.'
```

- Codex's built-in sandbox is active.
- Codex's approval prompts are active.
- The sub-agent is told to **only** generate the image and print the path. It does not need to `cp` or `sips`.
- The host (Claude Code in your terminal) reads the path from stdout and performs the file move/resize itself, in its own approved-tool context.
- Worst-case sub-agent compromise: a malicious prompt could still cause Codex to attempt unrelated commands. Writes outside the workspace are blocked by the sandbox, and elevated operations require approval prompts that, run non-interactively, fail rather than execute silently. **Writes inside the workspace remain possible under `workspace-write`** — the prompt instruction "do not copy or move" plus the sandbox + approval gating shrinks but does not eliminate blast radius. This is still strictly safer than Mode B's arbitrary-shell-without-approval posture.

This is the default for every recipe in SKILL.md.

### Mode B — Automated (opt-in)

Invocation:

```bash
codex exec --sandbox workspace-write --dangerously-bypass-approvals-and-sandbox \
  '$imagegen <PROMPT>. Save to <PATH> at exactly WxH pixels.'
```

- `--dangerously-bypass-approvals-and-sandbox` disables Codex's approval prompts AND its execution sandbox.
- The Codex sub-agent can now run arbitrary shell commands in your current working directory with no further confirmation.
- This is convenient for batch jobs but is a real trust hand-off. If the prompt source, the working directory, or the network path to OpenAI is somehow influenced by an attacker, the sub-agent can act on that influence.

**Use Mode B only when all of the following are true:**

1. You wrote the prompt yourself (or fully reviewed it).
2. Your current working directory contains no sensitive files you would not want overwritten or read.
3. You are batching many similar generations and the convenience of one-shot `cp`/`sips` is worth the trust hand-off.

When in doubt, stay on Mode A. The cost is one extra shell step performed by your host Claude Code session.

## What this skill never does on its own

- Read, modify, or transmit files outside the current working directory and `~/.codex/generated_images/`.
- Send your prompts anywhere except OpenAI's Codex CLI (which forwards to OpenAI's image-generation API).
- Store, log, or transmit your API keys. `OPENAI_API_KEY`, if set, remains in your environment only.

## Supply-chain notes

- This repo ships a prebuilt `dist/codex-imagegen.skill` zip. It contains exactly the files in `skill/`. You can verify with `unzip -l dist/codex-imagegen.skill`.
- The skill itself runs no installer, no postinstall hook, and no third-party scripts. It only tells Claude how to invoke `codex exec` and post-process the result with `sips`/`convert`.
- If you'd rather not trust the prebuilt bundle, install via Option A or Option C in the README (symlink/copy directly from the `skill/` directory).
