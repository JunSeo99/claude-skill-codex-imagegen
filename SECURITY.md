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
- runs an ephemeral Codex session with a read-only sandbox in a new empty temporary directory;
- ignores user configuration and project rules;
- disables shell and unified execution, hooks, plugins, apps, browser, computer-use, and multi-agent features;
- forwards only an allowlist of runtime environment variables and no API credentials;
- appends a fixed instruction that treats the brief as untrusted image content and permits only built-in image generation;
- constrains the final message to a JSON object containing generated PNG paths;
- accepts only existing, non-symlink `.png` files that canonically resolve under `$CODEX_HOME/generated_images/`, defaulting to `~/.codex/generated_images/`;
- prints only validated paths on stdout and suppresses the child transcript so the image brief is not echoed into host logs.

The host performs any copy, resize, or post-processing step in its own approved tool context. It must not copy a path that the launcher rejects.

## Prompt files

Write prompt files with the host's file-write tool. Do not construct them with shell interpolation, `echo`, `printf`, or a shell variable. Prompt files may contain quotes, command-looking text, or other metacharacters safely because the launcher sends their contents over stdin rather than evaluating them.

Delete temporary prompt files after generation if they contain confidential project information.

## Credential and capability isolation

The distributed skill uses only the user's existing Codex login and subscription. It has no direct Image API path, does not request or read API credentials, and does not switch billing modes. The subprocess cannot use shell, browser, computer-use, plugins, apps, hooks, or multi-agent features.

## Supply-chain notes

- `dist/codex-imagegen.skill` contains the files from `skill/`; verify with `unzip -l dist/codex-imagegen.skill`.
- The skill has no installer, postinstall hook, or third-party download step.
- The safe launcher invokes only the locally resolved `codex` executable and does not use a shell.
- Transparent PNG verification is implemented by the bundled Python-standard-library validator; it does not download or execute third-party helpers.
- To avoid the prebuilt bundle, install with the Skills CLI or symlink/copy the audited `skill/` directory.
