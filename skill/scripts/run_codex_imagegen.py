#!/usr/bin/env python3
"""Run Codex image generation without interpolating prompts into a shell command."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


SENSITIVE_ENV_MARKERS = ("API_KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Codex $imagegen from a UTF-8 prompt file in a read-only sandbox."
    )
    parser.add_argument("--prompt-file", required=True, help="UTF-8 file containing the image brief")
    parser.add_argument(
        "--image",
        action="append",
        default=[],
        help="Reference or source image to attach; repeat for multiple images",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Maximum Codex runtime in seconds (default: 300)",
    )
    return parser.parse_args()


def fail(message: str, exit_code: int = 2) -> None:
    print(f"run_codex_imagegen.py: {message}", file=sys.stderr)
    raise SystemExit(exit_code)


def read_prompt(path_text: str) -> str:
    path = Path(path_text).expanduser().resolve()
    if not path.is_file():
        fail(f"prompt file does not exist or is not a regular file: {path}")
    try:
        prompt = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        fail(f"could not read prompt file: {error}")
    if not prompt.strip():
        fail("prompt file is empty")
    if "$imagegen" not in prompt:
        fail('prompt file must explicitly invoke "$imagegen"')
    return prompt.rstrip() + (
        "\n\nUse only the built-in image-generation tool. Do not run shell commands or "
        "modify workspace files. Print each resulting PNG as an absolute path on its own line."
    )


def resolve_images(path_texts: list[str]) -> list[Path]:
    images: list[Path] = []
    for path_text in path_texts:
        path = Path(path_text).expanduser().resolve()
        if not path.is_file():
            fail(f"input image does not exist or is not a regular file: {path}")
        images.append(path)
    return images


def sanitized_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for name in list(environment):
        upper_name = name.upper()
        if any(marker in upper_name for marker in SENSITIVE_ENV_MARKERS):
            environment.pop(name, None)
    return environment


def extract_generated_paths(text: str, generated_root: Path) -> list[Path]:
    pattern = re.compile(re.escape(str(generated_root)) + r"/[^\s`\"']+?\.png", re.IGNORECASE)
    paths: list[Path] = []
    seen: set[Path] = set()

    for match in pattern.finditer(text):
        candidate = Path(match.group(0)).resolve()
        try:
            candidate.relative_to(generated_root)
        except ValueError:
            continue
        if candidate.suffix.lower() != ".png" or not candidate.is_file():
            continue
        if candidate not in seen:
            seen.add(candidate)
            paths.append(candidate)
    return paths


def main() -> None:
    args = parse_args()
    if args.timeout <= 0:
        fail("timeout must be a positive number")

    codex = shutil.which("codex")
    if codex is None:
        fail("codex CLI was not found on PATH")

    prompt = read_prompt(args.prompt_file)
    images = resolve_images(args.image)
    codex_root = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser().resolve()
    generated_root = (codex_root / "generated_images").resolve()

    with tempfile.TemporaryDirectory(prefix="codex-imagegen-") as temp_dir:
        last_message = Path(temp_dir) / "last-message.txt"
        command = [
            codex,
            "exec",
            "--skip-git-repo-check",
            "--ephemeral",
            "--sandbox",
            "read-only",
            "--output-last-message",
            str(last_message),
        ]
        for image in images:
            command.extend(["--image", str(image)])
        command.append("-")

        try:
            completed = subprocess.run(
                command,
                input=prompt,
                text=True,
                capture_output=True,
                timeout=args.timeout,
                check=False,
                env=sanitized_environment(),
            )
        except subprocess.TimeoutExpired:
            fail(f"codex timed out after {args.timeout} seconds", exit_code=124)
        except OSError as error:
            fail(f"could not start codex: {error}", exit_code=126)

        if completed.stdout:
            print(completed.stdout, file=sys.stderr, end="")
        if completed.stderr:
            print(completed.stderr, file=sys.stderr, end="")
        if completed.returncode != 0:
            fail(f"codex exited with status {completed.returncode}", completed.returncode)

        result_text = completed.stdout
        if last_message.is_file():
            result_text += "\n" + last_message.read_text(encoding="utf-8", errors="replace")

    generated_paths = extract_generated_paths(result_text, generated_root)
    if not generated_paths:
        fail(
            "codex did not return an existing PNG under "
            f"{generated_root}; refusing to copy an untrusted path"
        )

    for path in generated_paths:
        print(path)


if __name__ == "__main__":
    main()
