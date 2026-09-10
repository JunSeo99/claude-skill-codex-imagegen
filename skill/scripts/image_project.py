#!/usr/bin/env python3
"""Run a small image plan, checkpoint completed candidates, and build a local comparison gallery."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import fcntl
import hashlib
import html
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

from run_codex_imagegen import read_prompt, resolve_images

SCRIPTS = Path(__file__).resolve().parent


def read_plan(path: Path, single_prompt: str | None = None, images: list[str] | None = None) -> tuple[dict, str]:
    raw = (json.dumps({"title": "Image preview", "jobs": [{"id": "image", "prompt_file": single_prompt,
           "images": images or []}]}).encode() if single_prompt else path.read_bytes())
    if len(raw) > 128 * 1024:
        raise ValueError("plan exceeds 128 KiB")
    plan = json.loads(raw)
    if not isinstance(plan, dict) or set(plan) - {"title", "jobs"}:
        raise ValueError("plan must contain title and jobs only")
    jobs = plan.get("jobs")
    if not isinstance(jobs, list) or not 1 <= len(jobs) <= 8:
        raise ValueError("plan needs 1–8 jobs")
    digest = hashlib.sha256()
    ids = set()
    for job in jobs:
        if not isinstance(job, dict) or set(job) - {"id", "label", "prompt_file", "images"}:
            raise ValueError("unknown job fields")
        job_id = job.get("id", "")
        if not isinstance(job_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,47}", job_id) or job_id in ids:
            raise ValueError("job IDs must be unique lowercase filename slugs")
        ids.add(job_id)
        prompt = path.parent / job["prompt_file"]
        digest.update(read_prompt(str(prompt)).encode())
        job["prompt_file"] = str(prompt.resolve())
        references = job.get("images", [])
        if not isinstance(references, list) or not all(isinstance(p, str) for p in references):
            raise ValueError("images must be an ordered list of paths")
        images = resolve_images([str(path.parent / p) for p in references])
        for image in images:
            digest.update(image.read_bytes())
        job["images"] = [str(image) for image in images]
    digest.update(json.dumps(plan, sort_keys=True, ensure_ascii=False).encode())
    return plan, digest.hexdigest()


def gallery(plan: dict, state: dict, target: Path) -> None:
    cards = []
    for index, job in enumerate(plan["jobs"], 1):
        job_id = job["id"]
        if job_id in state["completed"]:
            caption = html.escape(str(job.get("label", job_id)))
            cards.append(f'<figure><a href="{job_id}.png"><img src="{job_id}.png" alt="{caption}"></a>'
                         f'<figcaption><b>{index:02d} · {caption}</b><br>{job_id}.png</figcaption></figure>')
    title = html.escape(str(plan.get("title", "Image directions")))
    refresh = '<meta http-equiv="refresh" content="5">' if state.get("status") in {"queued", "running"} else ''
    progress = f'{len(state["completed"])} of {len(plan["jobs"])} images ready.'
    page = ('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">' + refresh +
            '<title>' + title + '</title><style>body{margin:0;padding:5vw;background:#f5f2ed;color:#202420;'
            'font:16px/1.6 system-ui}h1{font-size:clamp(28px,4vw,56px);letter-spacing:-.04em;line-height:1.1}'
            'main{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,320px),1fr));gap:24px}'
            'figure{margin:0;background:white}img{display:block;width:100%;aspect-ratio:1;object-fit:contain}'
            'figcaption{padding:20px}a:focus-visible{outline:3px solid #235d48}p{max-width:65ch}</style>'
            f'<h1>{title}</h1><p>{progress} Open an image at full size, then reply with a number '
            'and the change you want.</p><main>' + ''.join(cards) + '</main></html>')
    (target / "index.html").write_text(page, encoding="utf-8")


def save_state(target: Path, state: dict, plan: dict) -> None:
    state["updated_at"] = time.time()
    pending = target / "manifest.tmp"
    pending.write_text(json.dumps(state, indent=2), encoding="utf-8")
    pending.replace(target / "manifest.json")
    gallery(plan, state, target)


def generate_one(job: dict, target: Path) -> dict:
    command = [sys.executable, str(SCRIPTS / "run_codex_imagegen.py"),
               "--prompt-file", job["prompt_file"], "--stats"]
    for image in job["images"]:
        command += ["--image", image]
    result = subprocess.run(command, stdout=subprocess.PIPE, text=True, check=False)
    if result.returncode:
        raise RuntimeError(f"launcher exited {result.returncode}; inspect worker.log before resuming")
    paths = result.stdout.splitlines()
    if len(paths) != 1 or not Path(paths[0]).is_file():
        raise RuntimeError("expected one image; do not regenerate automatically")
    destination = target / (job["id"] + ".png")
    with destination.open("xb") as output, Path(paths[0]).open("rb") as source:
        shutil.copyfileobj(source, output)
    return {"path": destination.name, "label": job.get("label", job["id"]),
            "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
            "image_model": "managed by Codex; not reported", "review": "pending"}


def run_jobs(plan: dict, state: dict, target: Path, workers: int) -> None:
    pending_jobs = iter([j for j in plan["jobs"] if j["id"] not in state["completed"]])
    state.update(status="running", pid=os.getpid(), errors={}, running=[])
    save_state(target, state, plan)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        active = {}
        def submit_next() -> None:
            job = next(pending_jobs, None)
            if job:
                active[pool.submit(generate_one, job, target)] = job["id"]
        for _ in range(workers):
            submit_next()
        while active:
            state["running"] = list(active.values())
            save_state(target, state, plan)
            done, _ = wait(active, return_when=FIRST_COMPLETED)
            for future in done:
                job_id = active.pop(future)
                try:
                    state["completed"][job_id] = future.result()
                except Exception as error:
                    state["errors"][job_id] = str(error)[:300]
            # After a failure, finish already-running calls but launch no more.
            if not state["errors"]:
                for _ in done:
                    submit_next()
            save_state(target, state, plan)
    state.update(status="failed" if state["errors"] else "complete", running=[])
    save_state(target, state, plan)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--plan")
    source.add_argument("--prompt-file", help="Shortcut for a single image")
    parser.add_argument("--image", action="append", default=[])
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--background", action="store_true", help="Detach worker and return immediately")
    parser.add_argument("--status", action="store_true", help="Read local job status without calling Codex")
    parser.add_argument("--workers", type=int, choices=range(1, 5), default=2)
    args = parser.parse_args()
    target = Path(args.out_dir).expanduser().absolute()
    if target.is_symlink():
        parser.error("out-dir must not be a symlink")
    if args.status:
        try:
            state = json.loads((target / "manifest.json").read_text())
        except (OSError, ValueError) as error:
            parser.error(f"cannot read job status: {error}")
        if state.get("status") == "running" and state.get("pid"):
            try:
                os.kill(state["pid"], 0)
            except ProcessLookupError:
                state["status"] = "interrupted"
        print(json.dumps({**state, "gallery": str(target / "index.html")}, ensure_ascii=False))
        return
    if not (args.plan or args.prompt_file) or (args.image and not args.prompt_file):
        parser.error("provide --plan or --prompt-file; --image belongs to --prompt-file")
    try:
        plan, digest = read_plan(Path(args.plan).expanduser().resolve() if args.plan else Path.cwd() / "plan.json",
                                 args.prompt_file, args.image)
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.error(str(error))
    if args.dry_run:
        print(json.dumps({"backend": "codex", "jobs": [j["id"] for j in plan["jobs"]],
                          "generation_calls": len(plan["jobs"]), "workers": args.workers, "network": False}))
        return
    if not args.resume:
        if target.exists():
            parser.error("out-dir exists; use --resume or a new directory")
        target.mkdir(parents=True)
    elif not target.is_dir():
        parser.error("cannot resume a missing directory")
    with (target / ".worker.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.error("a worker is already running for this directory")
        state = {"plan_sha256": digest, "backend": "codex", "completed": {}, "status": "queued", "total": len(plan["jobs"])}
        if args.resume:
            state = json.loads((target / "manifest.json").read_text())
            if state["plan_sha256"] != digest or state["backend"] != "codex":
                parser.error("plan or references changed; use a new out-dir")
        for job in plan["jobs"]:
            destination = target / (job["id"] + ".png")
            if job["id"] in state["completed"]:
                if destination.is_symlink() or not destination.is_file() or hashlib.sha256(destination.read_bytes()).hexdigest() != state["completed"][job["id"]]["sha256"]:
                    parser.error(f"completed image changed or missing: {job['id']}")
            elif destination.exists() or destination.is_symlink():
                parser.error(f"untracked output exists: {destination}")
        if args.background:
            snapshot = target / ".request-plan.json"
            snapshot.write_text(json.dumps(plan), encoding="utf-8")
            state.update(status="queued", pid=None)
            save_state(target, state, plan)
            command = [sys.executable, str(Path(__file__).resolve()), "--plan", str(snapshot),
                       "--out-dir", str(target), "--resume", "--workers", str(args.workers)]
            # Child must acquire the lock; release it before spawning.
            fcntl.flock(lock, fcntl.LOCK_UN)
            with (target / "worker.log").open("a") as log:
                child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                         start_new_session=True, close_fds=True)
            print(json.dumps({"status": "started", "pid": child.pid, "job_dir": str(target),
                              "gallery": str(target / "index.html"), "total": len(plan["jobs"])}))
            return
        run_jobs(plan, state, target, args.workers)
        print(json.dumps({"status": state["status"], "gallery": str(target / "index.html"),
                          "completed": len(state["completed"]), "total": len(plan["jobs"])}))
        if state["status"] == "failed":
            raise SystemExit(1)


if __name__ == "__main__":
    main()
