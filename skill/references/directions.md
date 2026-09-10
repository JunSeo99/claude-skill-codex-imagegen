# Distinct candidates, easy selection

Honor a specified count. For an unspecified “a few options”, make three. Keep
purpose, copy, product identity, and aspect ratio fixed; vary a meaningful design
choice such as photographic scene, graphic composition, or illustration medium.
Give candidates short names and stable IDs. Each must be a separate full-size image,
not panels painted into one generated contact sheet. No extra final render before
the user selects unless they explicitly delegated selection.

Write one short `$imagegen` brief per candidate, then a JSON plan. Paths are relative
to the plan file; all inputs are validated before the first generation call.

```json
{
  "title": "Coffee campaign directions",
  "jobs": [
    {"id": "a-studio", "label": "Warm studio photograph", "prompt_file": "a.txt"},
    {"id": "b-graphic", "label": "Bold graphic composition", "prompt_file": "b.txt"},
    {"id": "c-paper", "label": "Handmade paper illustration", "prompt_file": "c.txt"}
  ]
}
```

```bash
python3 "<SKILL_DIR>/scripts/image_project.py" --plan "<PLAN.json>" --out-dir "<NEW_DIR>" --background --workers 2
python3 "<SKILL_DIR>/scripts/image_project.py" --out-dir "<NEW_DIR>" --status
```

Optional `images` on each job is an ordered list of reference paths. Use the
`--prompt-file` shortcut for one image. The helper invokes Codex once per
candidate, saves separate PNGs, and builds `index.html` plus `manifest.json` locally.
The gallery costs no model tokens and can be opened in a browser. Show images in
Claude as well; do not make opening HTML a requirement to choose.

`--dry-run` checks a plan without generation. On a failure, successful candidates
remain available. Inspect the failure before using `--resume`; completed files and
input hashes are verified, then skipped. A changed plan requires a new output folder.
Background execution returns immediately; Claude can continue other requested work.
Status is local JSON: queued, running, complete, failed, or interrupted. Read errors
and `worker.log` on failure. At most `--workers` calls run together (default 2, max 4).
After a failure, already-running calls finish and are saved; queued calls stop.
Do not increase concurrency automatically on rate limits. Parallelism reduces
waiting, not tokens per image. The machine must remain awake for workers to run.
Do not resume automatically after an ambiguous timeout: it may have generated an image.
The helper accepts up to eight jobs per plan. Larger requested sets need explicit
grouping with the total count kept visible; do not multiply variants unasked.

Claude reviews every candidate. The manifest says `pending` until a human/Claude
review is recorded; successful generation alone does not mean approval. Present
one sentence per option explaining the visible difference. Ask “Which number, and
what should change?” Edit the chosen PNG using editing.md. For “pick for me”, choose
against the user's stated use and give the reason; stop if the winner already passes.
