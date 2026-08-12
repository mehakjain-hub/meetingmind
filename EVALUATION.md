# Evaluation

This document covers accuracy/reliability findings from testing MeetingMind on real
audio (AMI Corpus clips + personal recordings), known limitations and why they were
scoped out of v1, and a summary of the bug-triage pass done before tagging v1.0.

## Test Setup

- **Samples:** AMI Corpus meeting clips (ES2002a/b, IS1000a/d, TS3003d) plus two
  personal recordings — a 2-speaker clip and a 1-speaker clip.
- **Environment:** MacBook Pro (M-series, CPU-only inference), `faster-whisper`
  (`small`/`medium`, int8), local PostgreSQL via Homebrew.
- **Method:** manual review of transcript accuracy, speaker diarization, and
  extracted summary/decisions/action-items/agenda-status against the actual audio.

## Pipeline Accuracy Findings

### Whisper transcription

- Transcription quality on clean, moderate-pace English audio is strong — accurate
  wording, reasonable punctuation before cleanup.
- **Accented English → proper noun mangling.** Names not in Whisper's vocabulary get
  phonetically garbled on heavier accents (e.g. "Ms. Reyes" transcribed as
  "MISRAEUS"). This is a Whisper-side limitation, not a pipeline bug — accepted as a
  known constraint for v1, documented here rather than "fixed," since there's no
  reliable way to correct a hallucinated proper noun without a name dictionary or a
  larger model, both out of scope for a free-tier CPU deployment.
- **Heavy-accent language misdetection.** In one test, strongly accented English
  audio was misdetected as Welsh at 89% confidence by Whisper `small`, and
  transcribed fluently — and wrongly — in the wrong language. Forcing
  `--language en` avoids this; auto-detect is not safe to rely on for accented
  English speakers. The upload page exposes this as an explicit "Force English"
  vs. "Auto-detect" choice for exactly this reason.

### Speaker diarization

- Initially logged as a "single-speaker collapse" bug during testing — investigation
  found this was a **test setup error**, not a pipeline bug: the specific clip used
  for that test genuinely only contained one speaker. Diarization performs correctly
  on multi-speaker clips (see AMI Corpus results and the 2-speaker personal
  recording). No fix was needed; the finding is included here for the record since
  it was flagged as a concern earlier in development.

### Transcript cleaning

- `clean.py`'s filler-word stripping left orphaned punctuation in some cases —
  stray leading/trailing commas, mixed adjacent punctuation (`", ."`), and
  double-terminal punctuation (`"word,."`) after removing a filler word adjacent to
  a comma. **Fixed** — `remove_fillers()` now collapses mixed punctuation runs and
  strips stray leading/trailing marks before capitalization.

### Multilingual / Hinglish (code-switching)

- Tested on a 37-minute Hindi-majority clip with frequent English code-switching.
  Both `small` and `medium` models handled pure Hindi segments well, but failed
  **inconsistently** on code-switched English words/phrases — sometimes silently
  dropped, sometimes hallucinated/garbled Devanagari output in their place.
- This is a **code-mixing failure, not a language-detection failure** — the model
  correctly identifies the dominant language, then breaks down specifically at the
  language-switch boundaries within a segment.
- This inconsistent skip-vs-hallucinate pattern is the primary evidence behind
  scoping v1 to English-only, with multilingual support deferred to v2. A `medium`
  model retest to rule out a script buffering issue (vs. genuine CPU processing
  time) was planned but not completed before this write-up — noted here as
  unresolved rather than silently dropped.

## Gemini API Reliability

- **503 (overloaded) errors are a known, external capacity issue**, not a pipeline
  bug — tied to `gemini-3.5-flash`'s early scaling phase after its May 2026 launch,
  not anything specific to this project's usage pattern.
- `extract.py` retries on 429/500/503 with exponential backoff (base 2s, up to 4
  attempts, ~2–9s between attempts). This window is intentionally short — it
  smooths over brief blips but will **not** ride out sustained congestion, which has
  been observed to last 30–120+ minutes during peak load. Accepted as-is: a longer
  backoff would make a single meeting's processing time unpredictable, which is
  worse for a live demo than a clear failure.
- **Practical finding:** 503s reproduce consistently during IST evening/night
  (which is US daytime/peak hours for Gemini's traffic). Running test batches in
  early IST morning (US overnight, off-peak) meaningfully reduces failure rates.
  Worth knowing if you're evaluating this project and hit repeated 503s during an
  IST evening session — it's very likely time-of-day load, not a broken pipeline.

## Bug-Triage Pass (pre-v1.0)

A full pass was done across every file in the pipeline, DB layer, and frontend
before tagging v1.0. Real, verified bugs found and fixed:

| Area | Bug | Fix |
|---|---|---|
| Database | Each `crud.py` function committed independently, breaking `session_scope()`'s rollback guarantee — a failure partway through saving one meeting could leave orphan rows | Changed to `session.flush()`; the caller's `session_scope()` now owns the transaction boundary |
| Database | `init_db.py` used bare relative imports, `ModuleNotFoundError` on run | Fixed to absolute `app.db.*` imports with `sys.path` anchored to project root |
| Database | `session.py` hardcoded `echo=True`, contradicting its own docstring — every SQL statement printed to console | Fixed default to `False` |
| Pipeline | `extract.py`: `model_dimp()` typo (not a real Pydantic method) — dormant crash bug, only triggers on transcripts long enough to need chunking | Fixed to `model_dump()` |
| Pipeline | `diarize.py` imported `app.db.session` only to immediately overwrite the one thing it imported — but importing it ran an unrelated DB-config check that could crash diarization for a Postgres reason | Removed the import; loads `.env` directly |
| Pipeline | `align.py`, `merge.py` used `sys.path.append()` instead of `.insert(0, ...)` — local modules could be shadowed by an identically-named third-party package | Switched to `insert(0, ...)` |
| Pipeline | `align.py`: leftover debug print, and `align()` called twice in the CLI test block (second result unused, doubled whisperX cost) | Removed both |
| Frontend | `theme.py`: agenda status color-coding used substring matching (`"cover" in v_lower`), which matches all three enum values since `"covered"` is a substring of `"partially_covered"` and `"not_covered"` — **every agenda item rendered as "covered," including ones that weren't** | Switched to exact-match against the real enum values; added a third `status-partial` visual state |
| Frontend | `export.py` had a `SyntaxError` — a dangling `else` with no matching `if` — the module didn't import at all | Fixed the control flow |
| Frontend | `export.py`: `footer()` was defined nested inside `header()` instead of as a sibling method — PDF page numbers never rendered | Moved to a proper class method |
| Frontend | `export.py`: `export_meeting_pdf()` was accidentally indented inside the `MeetingPDF` class without `self` — unreachable as a module-level function | Moved to module level |
| Frontend | `export.py`: `multi_cell()` doesn't reset the X cursor in the installed fpdf2 version, so a second `multi_cell` call after another crashed with "not enough horizontal space" | Added explicit `pdf.set_x(pdf.l_margin)` after every `multi_cell` call |
| Frontend | `1_upload.py`: finishing a second pipeline run left stale `results_data` from the previous meeting in `session_state`, so the Results page could show the wrong meeting until manually reloaded | Now clears `results_data` on completion, matching the pattern already used in the history page |
| Frontend | Pages read `st.session_state.pipeline_status` directly with no default — a page opened via direct link/bookmark before the main entrypoint ran could crash | Added a shared `ensure_session_defaults()` helper, called from every page |
| Dependencies | `requirements.txt` was missing `soundfile` entirely, despite `diarize.py` and `1_upload.py` both importing it — a fresh clone would install cleanly, then crash the first time anyone uploaded audio | Added `soundfile==0.13.1` |
| Dependencies | `fpdf2` was unpinned with an unresolved `# TODO: fill in your local version` | Pinned to `2.8.7`, the version tested against |
| Tests | `test_extraction.py`'s docstring pointed at a nonexistent module path (`python -m app.pipeline.test_extraction`) | Corrected to `python -m tests.test_extraction`, matching the file's actual location |
| Tests | `test_extraction.py`'s sample agenda text contained a literal garbled Whisper mis-transcription ("MISRAEUS") left over from copy-pasting real output | Corrected to the real name ("Ms. Reyes") |
| Repo hygiene | `docker-compose.yml`, `tests/test_db.py`, `tests/test_pipeline.py` existed as empty placeholder files — Docker and pytest coverage are both explicit v2 goals, so empty stubs looked like broken/incomplete work rather than a deliberate scope decision | Removed; will be added properly in v2 |
| Repo hygiene | `.gitignore`'s `sample_data/*.wav` pattern only matched files directly in `sample_data/`, not nested ones — AMI Corpus clips under `sample_data/ami/` were untracked but not actually ignored | Changed to `sample_data/**/*.wav` |

One AgendaStatus/status-key concern raised early in review turned out to be a
non-issue: the field name guess (`status_key="status"`) was correct, and the
frontend's status-coloring function already branched on all three enum values —
the actual bug there was the substring-matching logic itself (see table above),
not a missing/wrong field name.

## Known Limitations (Scoped Out of v1, Deferred to v2)

- **Multilingual / code-switching support** — see Hinglish finding above.
- **Proper noun mangling on accented speech** — Whisper-side limitation, not
  correctable without a name dictionary or larger model.
- **Sustained Gemini free-tier congestion** — retry logic smooths brief blips only;
  a 30–120+ minute outage will fail the request rather than queue it.
- **~15-minute input cap** — a deliberate design decision to keep inference times
  reasonable on free-tier CPU compute, documented in the README rather than a
  hidden limitation.
- **No automated test coverage** — `test_extraction.py` is a manual integration
  script, not a pytest suite. Formal test coverage is a v2 goal.