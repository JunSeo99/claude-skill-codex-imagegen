from __future__ import annotations

import binascii
import importlib.util
import io
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import threading
import time
import tempfile
import unittest
from unittest import mock
import zipfile
import zlib


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skill"
RUNNER_PATH = SKILL / "scripts" / "run_codex_imagegen.py"
ALPHA_PATH = SKILL / "scripts" / "verify_png_alpha.py"
BUNDLE_PATH = ROOT / "dist" / "codex-imagegen.skill"
TRANSPARENT_FIXTURE = ROOT / "tests" / "fixtures" / "transparent-e2e.png"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUNNER = load_module("run_codex_imagegen", RUNNER_PATH)
ALPHA = load_module("verify_png_alpha", ALPHA_PATH)
sys.path.insert(0, str(SKILL / "scripts"))
PROJECT = load_module("image_project", SKILL / "scripts" / "image_project.py")


def png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    crc = binascii.crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)


def write_rgba_png(path: Path, width: int, height: int, pixels: list[tuple[int, int, int, int]]) -> None:
    if len(pixels) != width * height:
        raise ValueError("pixel count does not match dimensions")
    scanlines = bytearray()
    for row_index in range(height):
        scanlines.append(0)
        row = pixels[row_index * width : (row_index + 1) * width]
        for pixel in row:
            scanlines.extend(pixel)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    path.write_bytes(
        ALPHA.PNG_SIGNATURE
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", zlib.compress(bytes(scanlines)))
        + png_chunk(b"IEND", b"")
    )


class AlphaValidatorTests(unittest.TestCase):
    def test_live_end_to_end_fixture_keeps_real_alpha(self) -> None:
        metrics = ALPHA.inspect_alpha(TRANSPARENT_FIXTURE, require_transparent_corners=True)
        self.assertEqual(metrics["color_type"], "rgba")
        self.assertEqual(metrics["alpha_min"], 0)
        self.assertEqual(metrics["alpha_max"], 255)
        self.assertGreater(metrics["transparent_pixels"], 0)
        self.assertGreater(metrics["partial_pixels"], 0)
        self.assertGreater(metrics["opaque_pixels"], 0)

    def test_accepts_real_alpha_and_transparent_corners(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "transparent.png"
            pixels = [(255, 128, 0, 0)] * 9
            pixels[1] = (255, 128, 0, 128)
            pixels[4] = (255, 128, 0, 255)
            write_rgba_png(path, 3, 3, pixels)

            metrics = ALPHA.inspect_alpha(path, require_transparent_corners=True)

            self.assertEqual(metrics["alpha_min"], 0)
            self.assertEqual(metrics["alpha_max"], 255)
            self.assertEqual(metrics["corner_alpha"], [0, 0, 0, 0])
            self.assertEqual(metrics["partial_pixels"], 1)

    def test_rejects_opaque_png(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "opaque.png"
            write_rgba_png(path, 2, 2, [(0, 0, 0, 255)] * 4)
            with self.assertRaises(SystemExit):
                ALPHA.inspect_alpha(path, require_transparent_corners=True)


class LauncherBoundaryTests(unittest.TestCase):
    def test_environment_is_allowlisted(self) -> None:
        source = {
            "HOME": "/tmp/home",
            "PATH": "/usr/bin",
            "PROJECT_ACCESS_TOKEN": "must-not-pass",
            "UNRELATED_VALUE": "must-not-pass",
        }
        with mock.patch.dict(os.environ, source, clear=True):
            environment = RUNNER.sanitized_environment()
        self.assertEqual(environment, {"HOME": "/tmp/home", "PATH": "/usr/bin"})

    def test_structured_paths_must_stay_inside_generated_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "generated_images"
            trusted = root / "session" / "asset.png"
            trusted.parent.mkdir(parents=True)
            write_rgba_png(trusted, 2, 2, [(0, 0, 0, 0), (0, 0, 0, 255)] * 2)

            valid = json.dumps({"generated_png_paths": [str(trusted)]})
            self.assertEqual(RUNNER.extract_generated_paths(valid, root.resolve()), [trusted.resolve()])

            escaped = json.dumps({"generated_png_paths": [str(Path(temp_dir) / "outside.png")]})
            self.assertEqual(RUNNER.extract_generated_paths(escaped, root.resolve()), [])
            self.assertEqual(RUNNER.extract_generated_paths(f"prefix {valid}", root.resolve()), [])
            self.assertEqual(
                RUNNER.extract_generated_paths(
                    json.dumps({"generated_png_paths": [str(trusted)], "extra": "data"}),
                    root.resolve(),
                ),
                [],
            )
            duplicate = json.dumps({"generated_png_paths": [str(trusted), str(trusted)]})
            self.assertEqual(RUNNER.extract_generated_paths(duplicate, root.resolve()), [])

    def test_launcher_disables_non_image_capabilities(self) -> None:
        source = RUNNER_PATH.read_text(encoding="utf-8")
        for required in (
            '"--ignore-user-config"',
            '"--ignore-rules"',
            '"read-only"',
            '"shell_tool"',
            '"unified_exec"',
            '"hooks"',
            '"plugins"',
            '"apps"',
            '"browser_use"',
            '"computer_use"',
            '"multi_agent"',
            '"--output-schema"',
            '["--", "-"]',
        ):
            self.assertIn(required, source)
        self.assertNotIn("shell" + "=True", source)

    def test_model_arguments(self) -> None:
        self.assertEqual(RUNNER.model_arguments(None, None), [])
        self.assertEqual(RUNNER.model_arguments("gpt-5.6-luna", None), ["-m", "gpt-5.6-luna"])
        self.assertEqual(
            RUNNER.model_arguments("gpt-5.6-luna", "none"),
            ["-m", "gpt-5.6-luna", "-c", 'model_reasoning_effort="none"'],
        )

    def test_codex_error_message_reads_only_the_structured_error(self) -> None:
        stderr = "\n".join(
            (
                "model: bogus-model",
                "user",
                "$imagegen secret brief line that must never be echoed",
                "warning: Model metadata for `bogus-model` not found.",
                'ERROR: {"type":"error","status":400,"error":{"type":"invalid_request_error",'
                '"message":"The \'bogus-model\' model is not supported when using Codex with a ChatGPT account."}}',
            )
        )
        message = RUNNER.codex_error_message(stderr)
        self.assertEqual(
            message,
            "The 'bogus-model' model is not supported when using Codex with a ChatGPT account.",
        )
        self.assertNotIn("secret brief", message)
        self.assertTrue(RUNNER.model_was_rejected(stderr))
        self.assertFalse(RUNNER.model_was_rejected("user\n$imagegen brief\nERROR: not json"))
        self.assertEqual(RUNNER.codex_error_message("plain failure text"), "")
        long_message = json.dumps({"error": {"message": "x" * 1000}})
        self.assertEqual(len(RUNNER.codex_error_message(f"ERROR: {long_message}")), RUNNER.MAX_ERROR_MESSAGE_CHARS)

    def test_launcher_retries_once_on_default_model_when_slug_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            codex_home = Path(temp_dir) / "codex-home"
            trusted = codex_home / "generated_images" / "session" / "exec-1.png"
            trusted.parent.mkdir(parents=True)
            write_rgba_png(trusted, 2, 2, [(0, 0, 0, 0), (0, 0, 0, 255)] * 2)
            prompt_file = Path(temp_dir) / "brief.txt"
            prompt_file.write_text("$imagegen\nUse case: test\n", encoding="utf-8")

            commands: list[list[str]] = []

            def fake_run(command, **kwargs):
                commands.append(list(command))
                if "-m" in command:
                    return subprocess.CompletedProcess(
                        command,
                        1,
                        stderr='ERROR: {"error":{"message":"The \'gpt-old\' model is not supported when using Codex with a ChatGPT account."}}',
                    )
                last_message = Path(command[command.index("--output-last-message") + 1])
                last_message.write_text(json.dumps({"generated_png_paths": [str(trusted)]}), encoding="utf-8")
                return subprocess.CompletedProcess(command, 0, stderr="")

            argv = [
                "run_codex_imagegen.py",
                "--prompt-file",
                str(prompt_file),
                "--model",
                "gpt-old",
                "--reasoning-effort",
                "none",
                "--allow-default-model-fallback",
            ]
            with mock.patch.dict(os.environ, {"CODEX_HOME": str(codex_home), "PATH": "/usr/bin"}, clear=True), \
                mock.patch.object(RUNNER.shutil, "which", return_value="/usr/bin/codex"), \
                mock.patch.object(RUNNER.subprocess, "run", side_effect=fake_run), \
                mock.patch.object(sys, "argv", argv), \
                mock.patch("sys.stdout") as stdout, \
                mock.patch("sys.stderr") as stderr:
                RUNNER.main()

            self.assertEqual(len(commands), 2)
            self.assertEqual(commands[0][:2], ["/usr/bin/codex", "exec"])
            self.assertEqual(commands[0][2:6], ["-m", "gpt-old", "-c", 'model_reasoning_effort="none"'])
            self.assertNotIn("-m", commands[1])
            self.assertNotIn('model_reasoning_effort="none"', commands[1])
            self.assertIn("skills.include_instructions=false", commands[1])
            for command in commands:
                self.assertEqual(command[-2:], ["--", "-"])
                self.assertIn("--ignore-user-config", command)
            printed = "".join(call.args[0] for call in stdout.write.call_args_list)
            self.assertEqual(printed.strip(), str(trusted.resolve()))
            notices = "".join(call.args[0] for call in stderr.write.call_args_list)
            self.assertIn("retrying with the account default model", notices)
            self.assertNotIn("Use case: test", notices)

    def test_default_is_light_relay_and_no_automatic_upgrade(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            prompt = Path(temp_dir) / "brief.txt"
            prompt.write_text("$imagegen\nOne image of a cup.")
            failure = subprocess.CompletedProcess([], 1, stderr='ERROR: {"error":{"message":"model is not supported"}}')
            with mock.patch.object(sys, "argv", ["runner", "--prompt-file", str(prompt)]), \
                mock.patch.object(RUNNER.shutil, "which", return_value="codex"), \
                mock.patch.object(RUNNER.subprocess, "run", return_value=failure) as run, \
                mock.patch("sys.stderr", new_callable=io.StringIO):
                with self.assertRaises(SystemExit):
                    RUNNER.main()
            self.assertEqual(run.call_count, 1)
            command = run.call_args.args[0]
            self.assertEqual(command[command.index("-m") + 1], "gpt-5.6-luna")
            self.assertIn('model_reasoning_effort="none"', command)
            self.assertIn("skills.include_instructions=false", command)
            self.assertEqual(run.call_args.kwargs["input"], "$imagegen\nOne image of a cup.")

    def test_rejects_disguised_png_and_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            fake = root / "fake.png"
            fake.write_text("not an image")
            payload = json.dumps({"generated_png_paths": [str(fake)]})
            self.assertEqual(RUNNER.extract_generated_paths(payload, root), [])
            link = root / "link.png"
            link.symlink_to(TRANSPARENT_FIXTURE)
            self.assertEqual(RUNNER.extract_generated_paths(json.dumps({"generated_png_paths": [str(link)]}), root), [])


class ProjectTests(unittest.TestCase):
    def make_plan(self, root: Path) -> Path:
        (root / "a.txt").write_text("$imagegen\nOne cup, no text.")
        (root / "b.txt").write_text("$imagegen\nOne paper cup, no text.")
        path = root / "plan.json"
        path.write_text(json.dumps({"title": "<script>private</script>", "jobs": [
            {"id": "a", "label": '<img onerror="alert(1)">', "prompt_file": "a.txt"},
            {"id": "b", "prompt_file": "b.txt"}]}))
        return path

    def test_preflight_rejects_bad_second_job_before_any_generation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            path = self.make_plan(root)
            (root / "b.txt").unlink()
            with mock.patch.object(sys, "argv", ["project", "--plan", str(path), "--out-dir", str(root / "out")]), \
                mock.patch.object(PROJECT.subprocess, "run") as run, mock.patch("sys.stderr", new_callable=io.StringIO):
                with self.assertRaises(SystemExit):
                    PROJECT.main()
            run.assert_not_called()

    def test_resume_skips_completed_and_gallery_escapes_labels(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            path = self.make_plan(root)
            out = root / "out"
            source = root / "source.png"
            shutil_copy = TRANSPARENT_FIXTURE.read_bytes()
            source.write_bytes(shutil_copy)
            argv = ["project", "--plan", str(path), "--out-dir", str(out), "--workers", "1"]
            good = subprocess.CompletedProcess([], 0, stdout=str(source) + "\n")
            bad = subprocess.CompletedProcess([], 1, stdout="")
            with mock.patch.object(sys, "argv", argv), \
                mock.patch.object(PROJECT.subprocess, "run", side_effect=[good, bad]), \
                mock.patch("sys.stderr", new_callable=io.StringIO):
                with self.assertRaises(SystemExit):
                    PROJECT.main()
            state = json.loads((out / "manifest.json").read_text())
            self.assertEqual(list(state["completed"]), ["a"])
            first = (out / "a.png").read_bytes()
            with mock.patch.object(sys, "argv", argv + ["--resume"]), \
                mock.patch.object(PROJECT.subprocess, "run", return_value=good) as run, \
                mock.patch("sys.stderr", new_callable=io.StringIO), mock.patch("sys.stdout", new_callable=io.StringIO):
                PROJECT.main()
            self.assertEqual(run.call_count, 1)
            self.assertIn(str((root / "b.txt").resolve()), run.call_args.args[0])
            self.assertEqual((out / "a.png").read_bytes(), first)
            page = (out / "index.html").read_text()
            self.assertNotIn("<script>", page)
            self.assertIn("&lt;img", page)
            self.assertEqual(len(json.loads((out / "manifest.json").read_text())["completed"]), 2)

    def test_plan_hash_changes_with_reference_or_brief(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            path = self.make_plan(root)
            first = PROJECT.read_plan(path)[1]
            (root / "a.txt").write_text("$imagegen\nChanged cup.")
            self.assertNotEqual(first, PROJECT.read_plan(path)[1])

    def test_workers_overlap_and_stop_queued_jobs_after_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            plan = {"jobs": [{"id": name} for name in ("a", "b", "c")]}
            state = {"completed": {}}
            barrier = threading.Barrier(2)
            started = []
            def generate(job, out):
                started.append(job["id"])
                barrier.wait(timeout=3)
                if job["id"] == "a":
                    raise RuntimeError("quota exhausted")
                time.sleep(0.1)
                return {"path": "b.png"}
            with mock.patch.object(PROJECT, "generate_one", side_effect=generate):
                PROJECT.run_jobs(plan, state, target, 2)
            self.assertCountEqual(started, ["a", "b"])
            self.assertEqual(state["status"], "failed")
            self.assertIn("b", state["completed"])
            self.assertIn("a", state["errors"])

    def test_background_detaches_and_status_does_not_generate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            path = self.make_plan(root)
            out = root / "out"
            with mock.patch.object(sys, "argv", ["project", "--plan", str(path), "--out-dir", str(out), "--background"]), \
                mock.patch.object(PROJECT.subprocess, "Popen") as popen, \
                mock.patch.object(PROJECT, "run_jobs") as run, mock.patch("sys.stdout", new_callable=io.StringIO) as stdout:
                popen.return_value.pid = 123
                PROJECT.main()
            run.assert_not_called()
            self.assertEqual(json.loads(stdout.getvalue())["status"], "started")
            self.assertTrue(popen.call_args.kwargs["start_new_session"])
            self.assertTrue(popen.call_args.kwargs["close_fds"])
            self.assertEqual(popen.call_args.kwargs["stdin"], subprocess.DEVNULL)
            self.assertNotIn("--background", popen.call_args.args[0])
            self.assertEqual(PROJECT.read_plan(out / ".request-plan.json")[1], PROJECT.read_plan(path)[1])
            with mock.patch.object(sys, "argv", ["project", "--out-dir", str(out), "--status"]), \
                mock.patch.object(PROJECT.subprocess, "run") as run, mock.patch("sys.stdout", new_callable=io.StringIO) as stdout:
                PROJECT.main()
            run.assert_not_called()
            self.assertEqual(json.loads(stdout.getvalue())["status"], "queued")

    def test_detached_workers_complete_in_parallel_with_fake_codex(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.make_plan(root)
            binary_dir = root / "bin"
            binary_dir.mkdir()
            home = root / "codex-home"
            home.mkdir()
            fake = binary_dir / "codex"
            fake.write_text(f'''#!{sys.executable}
import json, os, pathlib, shutil, sys, time
started = time.time()
home = pathlib.Path(os.environ["CODEX_HOME"])
time.sleep(2)
folder = home / "generated_images" / str(os.getpid())
folder.mkdir(parents=True)
image = folder / "image.png"
shutil.copyfile({str(TRANSPARENT_FIXTURE)!r}, image)
pathlib.Path(sys.argv[sys.argv.index("--output-last-message") + 1]).write_text(json.dumps({{"generated_png_paths": [str(image)]}}))
(home / (str(os.getpid()) + ".json")).write_text(json.dumps({{"started": started, "ended": time.time()}}))
''')
            fake.chmod(0o755)
            out = root / "out"
            env = {**os.environ, "PATH": str(binary_dir) + os.pathsep + os.environ.get("PATH", ""), "CODEX_HOME": str(home)}
            started = time.monotonic()
            launch = subprocess.run([sys.executable, str(SKILL / "scripts/image_project.py"), "--plan", str(plan),
                "--out-dir", str(out), "--background", "--workers", "2"], env=env, capture_output=True, text=True, timeout=5)
            self.assertEqual(launch.returncode, 0, launch.stderr)
            self.assertLess(time.monotonic() - started, 2)
            self.assertEqual(json.loads(launch.stdout)["status"], "started")
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                state = json.loads((out / "manifest.json").read_text())
                if state["status"] in {"complete", "failed"}:
                    break
                time.sleep(0.1)
            self.assertEqual(state["status"], "complete", (out / "worker.log").read_text())
            self.assertEqual(len(state["completed"]), 2)
            timings = [json.loads(p.read_text()) for p in home.glob("*.json")]
            self.assertEqual(len(timings), 2)
            self.assertLess(max(t["started"] for t in timings), min(t["ended"] for t in timings))

    def test_single_prompt_shortcut_validates_without_generation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            prompt = root / "brief.txt"
            prompt.write_text("$imagegen\nA cup.")
            with mock.patch.object(sys, "argv", ["project", "--prompt-file", str(prompt), "--out-dir", str(root / "out"), "--dry-run"]), \
                mock.patch.object(PROJECT.subprocess, "run") as run, mock.patch("sys.stdout", new_callable=io.StringIO) as stdout:
                PROJECT.main()
            self.assertEqual(json.loads(stdout.getvalue())["generation_calls"], 1)
            self.assertFalse((root / "out").exists())
            run.assert_not_called()

    def test_rejects_duplicate_ids_path_escape_and_unsupported_controls(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            path = self.make_plan(root)
            original = json.loads(path.read_text())
            for extra in [{"id": "../escape"}, {"id": "a"}, {"image_model": "sunburst"}]:
                plan = json.loads(json.dumps(original))
                plan["jobs"][1].update(extra)
                path.write_text(json.dumps(plan))
                with self.assertRaises(ValueError):
                    PROJECT.read_plan(path)


class RepositoryTests(unittest.TestCase):
    def test_skill_frontmatter_and_size(self) -> None:
        skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(skill_text.startswith("---\n"))
        frontmatter = skill_text.split("---", 2)[1]
        keys = {line.split(":", 1)[0] for line in frontmatter.splitlines() if ":" in line}
        self.assertEqual(keys, {"name", "description"})
        self.assertIn("name: codex-imagegen", frontmatter)
        self.assertLess(len(skill_text.split()), 950)

    def test_forbidden_security_and_obsolete_transparency_claims_are_absent(self) -> None:
        forbidden_skill = (
            "dangerously-" + "bypass-approvals-and-sandbox",
            "OPENAI_" + "API_KEY",
            "gpt-image-" + "1.5",
            "remove_" + "chroma_key",
            "shell" + "=True",
            "os." + "system(",
        )
        for path in SKILL.rglob("*"):
            if (
                not path.is_file()
                or "__pycache__" in path.parts
                or path.suffix.lower() in {".pyc", ".png", ".jpg", ".jpeg", ".webp"}
            ):
                continue
            text = path.read_text(encoding="utf-8")
            for phrase in forbidden_skill:
                self.assertNotIn(phrase, text, f"{phrase!r} found in {path}")

        repository_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in ROOT.rglob("*.md")
            if ".git" not in path.parts
        ).lower()
        for phrase in (
            "does not support native " + "transparent",
            "no transparent png on " + "gpt-image-2",
            "gpt-image-2 has no native " + "transparent background",
        ):
            self.assertNotIn(phrase, repository_text)

    def test_bundle_matches_distributed_skill(self) -> None:
        expected = {
            path.relative_to(SKILL).as_posix(): path.read_bytes()
            for path in SKILL.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
        }
        with zipfile.ZipFile(BUNDLE_PATH) as bundle:
            actual = {
                name.removeprefix("codex-imagegen/"): bundle.read(name)
                for name in bundle.namelist()
                if not name.endswith("/")
            }
        self.assertEqual(actual, expected)

    def test_entrypoint_references_are_self_contained(self) -> None:
        skill_md = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        import re
        for target in re.findall(r"\]\((references/[^)]+)\)", skill_md):
            self.assertTrue((SKILL / target).is_file(), target)

    def test_readme_uses_skills_cli_and_cites_transparency(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("npx skills add", readme)
        self.assertIn("--skill codex-imagegen", readme)
        self.assertIn("developers.openai.com/api/docs/guides/image-generation", readme)

    def test_scripts_compile(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", *map(str, (SKILL / "scripts").glob("*.py"))],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
