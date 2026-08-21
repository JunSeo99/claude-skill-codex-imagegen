from __future__ import annotations

import binascii
import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
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
        ):
            self.assertIn(required, source)
        self.assertNotIn("shell" + "=True", source)


class RepositoryTests(unittest.TestCase):
    def test_skill_frontmatter_and_size(self) -> None:
        skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(skill_text.startswith("---\n"))
        frontmatter = skill_text.split("---", 2)[1]
        keys = {line.split(":", 1)[0] for line in frontmatter.splitlines() if ":" in line}
        self.assertEqual(keys, {"name", "description"})
        self.assertIn("name: codex-imagegen", frontmatter)
        self.assertLess(len(skill_text.splitlines()), 500)

    def test_forbidden_security_and_obsolete_transparency_claims_are_absent(self) -> None:
        forbidden_skill = (
            "dangerously-" + "bypass-approvals-and-sandbox",
            "OPENAI_" + "API_KEY",
            "gpt-image-" + "1.5",
            "remove_" + "chroma_key",
            "shell" + "=True",
            "os." + "system(",
            "subprocess." + "Popen",
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

    def test_readme_uses_skills_cli_and_cites_transparency(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("npx skills add", readme)
        self.assertIn("--skill codex-imagegen", readme)
        self.assertIn("GPT Image 2 supports transparent backgrounds in preview", readme)
        self.assertIn("developers.openai.com/api/docs/guides/image-generation", readme)

    def test_scripts_compile(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(RUNNER_PATH), str(ALPHA_PATH)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
