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
- supplies compact relay instructions that treat the brief and images as data and permit only built-in image generation;
- omits the skills catalog and replaces generic coding instructions for this subprocess; this does not change sandbox enforcement;
- constrains the final message to a JSON object containing generated PNG paths;
- accepts only existing, non-symlink `.png` files that canonically resolve under `$CODEX_HOME/generated_images/`, defaulting to `~/.codex/generated_images/`;
- prints only validated paths on stdout and suppresses the child transcript so the image brief is not echoed into host logs.

The host performs any copy, resize, or post-processing step in its own approved tool context. It must not copy a path that the launcher rejects.

## Background jobs

`image_project.py` runs the same launcher through a bounded thread pool (default two,
maximum four calls). `--background` detaches a Python worker using an argument-array
subprocess with stdin closed and stdout/stderr redirected to a local log. It does
not grant Codex any additional capabilities. Status and gallery rendering are local.

Plans are preflighted before generation. Output directories must be new unless
explicitly resuming; a process lock prevents concurrent workers for the same directory.
Resume checks the plan, brief/reference content, and completed-image hashes. After a
failure, already-running calls finish but no queued calls start. Timeouts are not
automatically retried. Gallery labels are HTML-escaped and no external resources load.

The manifest, gallery, request snapshot and worker log remain on the user's machine.
They can reveal local paths and labels, so do not publish them unless requested.

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
