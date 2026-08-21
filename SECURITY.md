# Security

## Reporting a vulnerability

Open a GitHub issue or email jun@indexfinger.org.

## Trust boundary

This skill starts the OpenAI Codex CLI as a sub-agent from a Claude Code session. The distributed skill therefore limits both what reaches the subprocess and which result paths the host will accept.

## Sandboxed Codex path

The skill has one Codex subscription execution path: `skill/scripts/run_codex_imagegen.py`.

The launcher:

- reads the image brief from a UTF-8 file and passes it to `codex exec` over stdin with a subprocess argument array;
- never places user prompt text inside a shell command;
- runs an ephemeral Codex session with a read-only shell sandbox;
- removes API keys, tokens, secrets, passwords, and credential variables from the Codex subprocess environment;
- appends a fixed instruction to use only the built-in image-generation tool and avoid shell commands or workspace changes;
- accepts only existing `.png` files that canonically resolve under `$CODEX_HOME/generated_images/`, defaulting to `~/.codex/generated_images/`;
- prints validated paths on stdout and sends Codex logs to stderr.

The host performs any copy, resize, or post-processing step in its own approved tool context. It must not copy a path that the launcher rejects.

## Prompt files

Write prompt files with the host's file-write tool. Do not construct them with shell interpolation, `echo`, `printf`, or a shell variable. Prompt files may contain quotes, command-looking text, or other metacharacters safely because the launcher sends their contents over stdin rather than evaluating them.

Delete temporary prompt files after generation if they contain confidential project information.

## Direct Image API path

Some advanced controls require Codex's bundled `image_gen.py` and an already configured `OPENAI_API_KEY`. This path runs directly in the host's approved context and may incur per-image API charges.

- Do not print, copy, log, or pass the API key on a command line.
- Do not switch from subscription usage to API billing without the user's request or confirmation.
- Prefer `--prompt-file` and explicit output paths.

## Supply-chain notes

- `dist/codex-imagegen.skill` contains the files from `skill/`; verify with `unzip -l dist/codex-imagegen.skill`.
- The skill has no installer, postinstall hook, or third-party download step.
- Runtime helpers are read from the user's existing Codex installation under `$CODEX_HOME/skills/.system/imagegen/`; the skill does not modify them.
- The safe launcher invokes only the locally resolved `codex` executable and does not use a shell.
- To avoid the prebuilt bundle, install with the Skills CLI or symlink/copy the audited `skill/` directory.
