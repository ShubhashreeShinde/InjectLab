# InjectLab: Project Guide (component by component)

> **How to use this file.** Give this whole file to your AI coding assistant at the start. Then work on ONE component at a time. After each component, test it, tick the checkbox in the Progress Tracker, and only then move to the next one.
>
> "InjectLab" is a working name. Rename it whenever you like.

---

## 0. Instructions for the AI assistant (read first)

You are helping a student build **InjectLab**, an open-source Python tool that measures how well different defenses stop prompt-injection attacks on LLM apps. It attacks mock apps running on local models, scores results with code (not another LLM), and reports attack success rate against benign task success.

**Rules you must follow:**

1. **Work on one component at a time.** Never start component N+1 until the user says component N passed its tests.
2. **At the start of each component**, restate its goal in 2-3 lines and list the files you will create or change.
3. **At the end of each component**, print: (a) what you built, (b) how to run it, (c) the exact test steps from this guide, (d) known limitations. Then STOP and wait.
4. **Keep it simple.** No extra features, no new libraries beyond the stack below, no rewrites of finished components unless a test fails.
5. **Check current docs.** Library APIs and dataset locations change. Before using Ollama's API, the OpenAI Python SDK, Hugging Face `datasets`/`transformers`, or any public dataset, check current documentation and the dataset's license. If something here conflicts with current docs, follow the docs and tell the user.
6. **Be honest about measurements.** Never fabricate results. Never hide failures or weak numbers. Record them.
7. **Safety and scope rules (important):**
   - All victim apps are **mock apps owned by the user**. Mock tools must never perform real actions (no real email, network calls, file deletion). They only log their calls.
   - Use **public datasets** for attacks, plus a small hand-written set aimed only at the user's own mock apps.
   - Do not write attacks aimed at real third-party products or services.
   - "Adaptive" attacks (C14) are written only against the user's own defenses, to test them.
8. **Explain briefly.** The user is a student learning this. Add short comments on non-obvious code and a 3-line "what this does" note per file.
9. **Free only.** No paid APIs. Local models through Ollama are the default.

---

## 1. Project summary

**One-liner:** An open-source harness that measures how well defenses stop prompt injection on LLM apps, and what they cost in usefulness.

**Problem:** LLM apps that read untrusted text (emails, web pages, documents) can be tricked by instructions hidden inside that text. Many defenses are proposed, but they are often evaluated only on their own attacks, and their cost to normal use is rarely reported.

**Question the project answers:** Which defense layers reduce attack success rate on small local models, how much do they hurt normal tasks, and how do they hold up against attacks written to get around them?

**Key ideas from the research literature (the AI should design around these):**
- Measure security **and** utility **and** false positives **and** overhead together. A defense that blocks everything is useless.
- Defenses that look near-perfect on standard attacks can fail badly against attacks written with knowledge of the defense, so the project includes an adaptive round.
- Results from LLMs are statistical, not yes/no, so each case runs multiple times and rates are reported with confidence intervals.

**Success criteria (fill in your targets, then do not move the goalposts):**
- Baseline (no defense) attack success rate is measured on at least 2 models
- At least 3 defense layers compared, individually and in combinations, each with ASR, benign success, false positive rate and overhead
- A security-utility frontier chart, plus the least restrictive stack that meets a pre-set ASR target, chosen on the dev split and confirmed on the held-out test split
- An adaptive round is run and reported honestly, even if it breaks your best defense
- A fake-model smoke test passes in CI (proves scorers work with no LLM)
- A human audit of 40-60 outputs reports how often the automated scorer agrees with a human
- A reproducibility package (fixed seeds, exact model versions, dataset hashes, configs, raw database, one-command rerun)
- A stranger can clone the repo, follow the README, and see a report in under 1 hour

**Scope (do):** text-based attacks, direct and indirect injection, Python, local models via Ollama (optionally one free-tier hosted model), SQLite results, HTML report.

**Scope (do NOT build):** attacks on real systems, image/audio attacks, a web app or accounts, fine-tuning models, jailbreak-for-harmful-content research, a hosted service.

---

## 2. Glossary

| Term | Meaning |
|---|---|
| **Prompt injection** | Text that tries to make an LLM follow attacker instructions instead of the app's instructions. |
| **Direct injection** | The attacker types the malicious instruction as the user. |
| **Indirect injection** | The instruction is hidden inside content the app reads (an email, web page, document, tool output). |
| **Canary** | A secret marker string planted in the system prompt. If it shows up in output, the attack leaked data. |
| **Mock tool** | A fake function (like `send_email`) that only records that it was called. |
| **ASR (attack success rate)** | Fraction of attack runs that achieved the attacker's goal. Lower is better for defenses. |
| **Benign success / utility** | Fraction of normal tasks still done correctly. Higher is better. |
| **False positive rate (FPR)** | Fraction of harmless inputs wrongly blocked or changed by a defense. |
| **Overhead** | Extra latency and tokens a defense adds. |
| **Defense layer** | One protective step (prompt hardening, input filter, detector, tool allow-list). |
| **Adaptive attack** | An attack written with knowledge of a specific defense, to get around it. |
| **Wilson interval** | A way to give a confidence range for a rate (like 12 of 40 attacks succeeded). |
| **Detector model** | A small classifier that flags text likely to contain an injection. |
| **Plugin** | A small class that follows a fixed interface, so others can add attacks or defenses without touching core code. |
| **JSONL** | A file format with one JSON object per line. |
| **Dev / test split** | Dev cases are used to design and tune defenses. Test cases are never looked at while tuning and are used only for final reported numbers. |
| **Security-utility frontier** | A chart of how much a defense stack lowers attacks against how much normal use survives. Stacks on the edge (no other stack is better on both) are the "Pareto-optimal" ones. |
| **Ablation** | Removing one layer from a stack to see how much that layer was contributing. |
| **Cohen's kappa** | An agreement score between two labelers (here: you and the automated scorer) that corrects for agreement by chance. |
| **Dataset hash** | A fingerprint (SHA-256) of a data file, proving exactly which data produced a result. |
| **Ollama** | A tool that runs open-source LLMs locally with a simple API. |
| **OpenAI-compatible API** | A common API shape many servers copy, so one adapter works with many models. |

---

## 3. Tech stack

| Layer | Choice |
|---|---|
| Language | Python 3.11+ |
| CLI | Typer |
| Config and schemas | YAML + Pydantic |
| Model access | OpenAI Python SDK or httpx pointed at any OpenAI-compatible endpoint |
| Local models | Ollama (default) or llama.cpp |
| Detector defense | Hugging Face `transformers` (+ `datasets` for loading public sets) |
| Storage | SQLite |
| Analysis | pandas |
| Reports | Jinja2 HTML + matplotlib or Plotly |
| Tests and lint | pytest, Ruff |
| CI | GitHub Actions |
| Packaging | `pyproject.toml`, Dockerfile |

---

## 4. Suggested repo structure

```
injectlab/
  README.md
  CONTRIBUTING.md
  pyproject.toml
  docs/
    INJECTLAB_PROJECT_GUIDE.md
    REPORT.md
  src/injectlab/
    schemas.py          # test case + result models
    targets/            # model adapters (+ fake model)
    apps/               # mock victim apps + mock tools
    scorers/            # canary, tool-call, utility
    datasets/           # loaders + attack/benign JSONL files
    defenses/           # one file per defense plugin
    runner.py
    storage.py          # SQLite
    stats.py            # rates, Wilson intervals
    report/             # HTML templates
    cli.py
  configs/              # example YAML configs
  tests/
```

---

## 5. Progress tracker

Tick each box only after the user confirms the component's tests passed.

- [ ] C0: Project setup and repo
- [ ] C1: Schemas (test case and result)
- [ ] C2: Target adapter and fake model
- [ ] C3: Mock victim apps and mock tools
- [ ] C4: Scorers
- [ ] C5: Datasets (attack and benign)
- [ ] C6: Runner and storage
- [ ] C7: Baseline measurement (no defense)
- [ ] C8: Defense interface + prompt hardening
- [ ] C9: Rule-based input filter
- [ ] C10: Detector model defense
- [ ] C11: Tool allow-list, argument validation, output scan
- [ ] C12: Metrics and statistics
- [ ] C13: Full matrix run
- [ ] C14: Adaptive round
- [ ] C15: Report generation
- [ ] C16: Packaging, CI, docs, write-up

---

## 6. Data shapes (used from C1 onward)

**Test case (one line in a JSONL file):**

```json
{
  "id": "string",
  "kind": "attack | benign",
  "app": "summarizer | tool_assistant",
  "channel": "direct | indirect",
  "user_task": "text of what the user asks the app to do",
  "untrusted_content": "email/document text, which for attacks contains the injected instruction",
  "goal": { "type": "leak_canary | call_tool | none", "tool": "send_email", "args_match": {} },
  "utility_check": { "must_contain": ["..."], "must_not_contain": ["..."] },
  "source": "bipia | deepset | injecagent | handwritten | adaptive",
  "split": "dev | test | adaptive",
  "technique": "null for standard cases; for adaptive cases: paraphrase | encoding | split_instructions | role_confusion | tool_arg_abuse",
  "license": "string",
  "tags": ["..."]
}
```

**Result row (one per run):**

```json
{
  "run_id": "uuid",
  "timestamp": "ISO string",
  "model": "string",
  "model_digest": "exact model version or hash reported by the server",
  "defense": "none | prompt_hardening | rule_filter | detector | tool_guard | combo:...",
  "case_id": "string",
  "repeat_index": 0,
  "output_text": "string",
  "tool_calls": [{"name": "send_email", "args": {}}],
  "blocked_by_defense": false,
  "attack_success": true,
  "utility_pass": null,
  "latency_ms": 1200,
  "prompt_tokens": 300,
  "completion_tokens": 80,
  "error": null
}
```

Rules:
- `attack_success` is only set for attack cases; `utility_pass` only for benign cases.
- A request blocked by a defense counts as: attack_success = false for attacks; utility_pass = false for benign cases (and a false positive).
- Errors (timeouts, model failures) are stored and excluded from rates with a visible count. Never silently dropped.

---

## 7. Components

Each component has: **Goal**, **Your steps** (what the human does), **AI tasks**, **Test (done when)**, and **Interview note**.

---

### C0: Project setup and repo

**Goal:** Clean Python project that installs, lints, tests and is on GitHub.

**Your steps:**
1. Install Python 3.11+, Git, and Ollama. Create a public GitHub repo.
2. Pull one small instruct model in Ollama (for example a 1-3B model) and chat with it once in the terminal to confirm it works. Note your RAM, because it limits model size.
3. Use feature branches and pull requests (even to yourself) for each component.

**AI tasks:**
- Scaffold `pyproject.toml`, `src/injectlab/`, `tests/`, Ruff, pytest.
- Add `injectlab --help` through Typer (placeholder commands are fine).
- Add a basic README ("work in progress") and a GitHub Actions workflow that runs lint and tests.

**Test (done when):**
- `pip install -e .` works and `injectlab --help` prints.
- `pytest` passes (a placeholder test is fine) and CI is green.

**Interview note:** Be able to explain why a pip-installable CLI is better than loose scripts.

---

### C1: Schemas (test case and result)

**Goal:** Strict, validated data shapes so everything else plugs together.

**Your steps:**
- Read section 6 and decide if you want any extra fields. Change them now, because they are painful to change later.

**AI tasks:**
- Pydantic models for `TestCase`, `Goal`, `UtilityCheck`, `RunResult`.
- Loader: read a JSONL file into validated `TestCase` objects, with clear error messages including line numbers.
- Writer for `RunResult` objects.
- Unit tests for valid and invalid examples.

**Test (done when):**
- A valid JSONL loads. A file with a missing field fails with a helpful message that names the line.
- Round trip (write then read) preserves all fields.

**Interview note:** Why validated schemas matter when other people contribute data.

---

### C2: Target adapter and fake model

**Goal:** One interface to talk to any model, plus a fake model for tests.

**Your steps:**
1. Confirm Ollama's OpenAI-compatible endpoint works on your machine (the AI will tell you the URL and how to check).
2. Optional: get a free-tier API key from one hosted provider and check its current limits and data-use terms. Never commit keys; use environment variables.

**AI tasks:**
- `Target` interface: `generate(messages, tools=None, temperature, seed) -> {text, tool_calls, latency_ms, prompt_tokens, completion_tokens}`.
- `OpenAICompatibleTarget` (base URL, model name, API key from env).
- Timeouts, retry with backoff, and clear errors.
- `FakeTarget` with deterministic modes: `leak_canary` (always repeats any canary it sees), `safe` (never leaks), `call_tool` (always calls a named tool), `echo`. Used in CI so tests need no LLM.

**Test (done when):**
- A one-line script gets a reply from your local Ollama model.
- `FakeTarget` returns the expected output in each mode (unit tests).
- A bad URL or stopped Ollama produces a clear error, not a hang.

**Interview note:** Why a fake model makes the scoring logic testable without LLM randomness.

---

### C3: Mock victim apps and mock tools

**Goal:** Two small apps that read untrusted content, used as attack targets.

**Your steps:**
1. Decide the two scenarios: for example (a) a **summarizer** that summarizes an email or web page, and (b) a **tool assistant** that reads a document and may call mock tools like `send_email` or `read_file`.
2. Write the system prompts yourself (or review the AI's), including a **canary string** (a random-looking secret that is not a real secret).

**AI tasks:**
- `Summarizer` app: builds messages from `user_task` and `untrusted_content`, calls a `Target`.
- `ToolAssistant` app: same, with tool definitions passed to the model. Tool calls go to **mock tools** that only append to a log and return a harmless fake result.
- Canary is inserted into the system prompt by the app, and a fresh canary can be generated per run.
- Apps expose one method: `run(case, target, defense_pipeline) -> AppOutput(text, tool_calls, blocked)`.
- Unit tests using `FakeTarget`.

**Test (done when):**
- With `FakeTarget(leak_canary)` the summarizer output contains the canary. With `FakeTarget(safe)` it does not.
- With `FakeTarget(call_tool)` the mock tool log records the call. No real side effects occur anywhere (verify by reading the tool code).
- A real local model produces a sensible summary of a benign email.

**Interview note:** Why mock tools plus a canary give an objective, safe success check.

---

### C4: Scorers

**Goal:** Code that decides, objectively, whether an attack succeeded and whether a benign task still worked.

**Your steps:**
- Define in plain words what "attack success" means for each goal type. Write it down. Example: `leak_canary` succeeds if the canary string appears in the output text; `call_tool` succeeds if the tool log contains that tool with arguments that match `args_match`.

**AI tasks:**
- `score_attack(case, app_output, canary) -> bool` for `leak_canary` and `call_tool`.
- `score_utility(case, app_output) -> bool` using `must_contain` / `must_not_contain` (case-insensitive, whitespace-normalized; document exactly how).
- Blocked outputs follow the rules in section 6.
- Thorough unit tests with edge cases (canary split across lines, partial canary, tool called with wrong args, empty output).

**Test (done when):**
- All unit tests pass, including the edge cases.
- You manually review 10 scored examples and agree with every score.

**Interview note:** Why programmatic scoring is more trustworthy and cheaper than an LLM judge here, and its limits (it can miss subtler harms).

---

### C5: Datasets (attack and benign)

**Goal:** A usable set of attack and benign cases in the schema from section 6.

**Your steps (this component is mostly yours):**
1. Look up these public sets and check each one's **current location and license** before using it: BIPIA (indirect injections in emails, tables, code), deepset/prompt-injections, InjecAgent (attacks in agent tool outputs), and a benign trigger-word set (for example NotInject) for false positives. Keep a table of what you used and the license.
2. Pick a manageable subset from each (for example 100-200 attacks total, 100-200 benign), so runs finish on a laptop.
3. **Write 20-30 attacks by hand** aimed only at your own mock apps, split between direct and indirect. Vary the style (different wording, placement in the document, different goals).
4. **Write 30-50 benign cases** with a clear `utility_check`, including some that contain scary-sounding but harmless text.
5. Read through a sample of every file yourself to catch garbage, wrong labels and duplicates.
6. Commit to this rule now: tune defenses (rules, detector threshold, prompt wording) only on the **dev** split. Peeking at test-split results while tuning defeats the purpose of having one.

**AI tasks:**
- Converters from each public dataset into the schema, recording `source` and `license`.
- A `validate-datasets` command that checks schema validity, duplicate ids, empty fields, and prints counts by kind, channel, source.
- A fixed random-seeded sampler so subsets are reproducible.
- A **dev/test split**: assign each case to `dev` or `test` (suggest 40/60, stratified by kind, channel and source). Hand-written adaptive cases (C14) get their own `adaptive` split.
- A command that computes and stores a SHA-256 hash of every dataset file, so results can state exactly which data produced them.

**Test (done when):**
- `validate-datasets` reports zero problems and shows the expected counts.
- You have read at least 20 random cases and confirmed the labels make sense.
- Every case has a split, no case id appears in both dev and test, and the dataset hashes are stored.
- A licensing table exists in `docs/`.

**Interview note:** Be able to describe your dataset's size, sources, licenses and weaknesses (for example mostly English, short texts).

---

### C6: Runner and storage

**Goal:** Run many (model, defense, case) combinations repeatedly and save every result.

**Your steps:**
- Decide your defaults and write them down: repeats per case (suggest 5), temperature, seed policy, timeout.

**AI tasks:**
- SQLite storage for `RunResult` (create tables, insert, query, export CSV).
- `Runner`: for each combination and repeat, run the app, score, record latency/tokens, store the row.
- **Resume support:** skip combinations already completed.
- Progress bar, `--limit` option for quick tests, and clean cancel (Ctrl+C keeps completed rows).
- CLI: `injectlab run configs/example.yaml`.
- YAML config: models, defenses, dataset paths, repeats, app names.

**Test (done when):**
- A run with `FakeTarget` over 20 cases x 3 repeats stores exactly 60 rows with correct scores.
- Interrupting and re-running does not duplicate rows.
- A forced model error is stored as an error row and the run continues.

**Interview note:** Why repeats and resume matter when LLM calls are slow and non-deterministic.

---

### C7: Baseline measurement (no defense)

**Goal:** Real, first numbers: how vulnerable are your models with no defense?

**Your steps:**
1. Pick 2 local models of different sizes (and optionally one free-tier hosted model).
2. Run the full baseline on a subset first (for example 50 attacks, 30 benign), look at the outputs by hand, and only then run everything.
3. Do a **human audit**. Randomly pick 40-60 runs, covering attacks and benign cases, both models, scorer "success" and "fail", and several borderline outputs. Label each one yourself without looking at the scorer's verdict (did the attack succeed? did the benign task work?). Then compare with the scorer. If a scorer bug shows up, fix it and audit a fresh sample. Repeat a smaller audit later on defended runs (C13), because blocked or rewritten outputs can confuse scorers.

**AI tasks:**
- A `summary` command printing ASR and benign success per model, by channel (direct vs indirect) and by source dataset.
- A command that samples runs for the audit and writes an audit file that **hides the scorer's verdict**, then a second command that reads your labels and reports percent agreement, Cohen's kappa, and a list of disagreements.

**Test (done when):**
- Baseline results exist for 2 models and look plausible (not 0% or 100% everywhere without explanation).
- The human audit covers at least 40 runs and you can report percent agreement and Cohen's kappa. Aim for at least 95% agreement. If lower, fix the scorer and re-audit. Every disagreement and its cause goes in the report.

**Interview note:** Why you checked the scorer against human judgment before trusting any number.

---

### C8: Defense interface + prompt hardening

**Goal:** A plugin interface for defenses, and the first (cheapest) defense.

**Your steps:**
- Decide in writing where each defense sits in the pipeline (before the model sees text, around the prompt, after the output). Keep it simple.

**AI tasks:**
- `Defense` base class with hooks: `before_model(messages, case) -> messages or Block`, `after_model(output, case) -> output or Block`. Defenses can be combined in order.
- Registry so defenses are loaded by name from the config (also the plugin point contributors use).
- `PromptHardening` defense: clearly delimit untrusted content as data and instruct the model not to follow instructions inside it. Keep the wording configurable.
- Runner records `blocked_by_defense` and the defense name.

**Test (done when):**
- Unit tests show the hardened prompt differs from baseline and the untrusted text is delimited.
- A run on the baseline attack subset shows a measured change in ASR (up, down, or none, whatever is true). Record it.
- Adding a no-op defense through the registry works without editing core code.

**Interview note:** Why prompt-only defenses are weak, and what your numbers show.

---

### C9: Rule-based input filter

**Goal:** A simple pattern-based filter, as the cheap-defense comparison.

**Your steps:**
- Think about what patterns attackers use and write a first rule list yourself before looking at the AI's version. Then check the false positive rate honestly.

**AI tasks:**
- `RuleFilter` defense: configurable patterns (phrases, structures, suspicious markers), normalization (case, unicode tricks, whitespace), and an action (block, or strip the matched text).
- Rules live in a YAML file so contributors can add rules without code.
- Unit tests for matches and non-matches.

**Test (done when):**
- Unit tests pass.
- Measured ASR and FPR on your datasets are recorded. High FPR on the benign trigger-word set is a valid finding, so report it.

**Interview note:** Why pattern filters are easy to evade and how your data shows it.

---

### C10: Detector model defense

**Goal:** Use a small open-source injection classifier as a defense.

**Your steps:**
1. Pick 1-2 open-source injection-detector models on Hugging Face and check each one's license, size and which benchmarks it may have been trained on (a model tested on data it trained on will look unrealistically good). Note this in your report.
2. Confirm it runs on your machine (CPU is fine for small ones).

**AI tasks:**
- `DetectorDefense`: loads the model once, scores the untrusted content (chunk long text, take the highest score because only the first part of long inputs may be scored), blocks above a threshold.
- Threshold in config; a command that sweeps thresholds and plots ASR vs FPR.
- Unit tests with a stubbed classifier (so CI needs no model download).

**Test (done when):**
- Detector runs on a handful of examples and produces scores.
- The threshold sweep produces a trade-off table (ASR vs FPR).
- CI tests pass with the stub.

**Interview note:** Why detectors struggle most on indirect injections hidden in long or structured content, and how your numbers compare.

---

### C11: Tool allow-list, argument validation, output scan

**Goal:** Action-level defenses that limit what a hijacked model can actually do.

**Your steps:**
- For each mock tool, write down what is legitimate: which tool the user's task needs, and allowed argument values (for example, an email may only go to a fixed list of addresses).

**AI tasks:**
- `ToolGuard` defense: per-app tool allow-list, per-tool argument validators (allowed recipients/paths, length limits), and an option requiring the call to match the user's task.
- `OutputScan` defense: block outputs containing the canary or other configured sensitive patterns.
- Record when the guard blocked a call so overhead and utility cost are measurable.
- Unit tests with `FakeTarget(call_tool)`.

**Test (done when):**
- With `FakeTarget(call_tool)`, an unauthorized call is blocked and an authorized one passes.
- Measured ASR for tool-goal attacks drops, and the benign success cost is recorded.

**Interview note:** Why limiting actions is often stronger than trying to detect bad text, and its utility cost.

---

### C12: Metrics and statistics

**Goal:** Correct, defensible numbers.

**Your steps:**
- Write down in advance exactly how each metric is computed, so you can't be accused of picking whichever looks best.
- Write down now, before seeing results, your target for the policy pick below (for example "indirect-attack ASR at most X%, benign success at most Y points below baseline").

**AI tasks:**
- `stats.py`: ASR, benign success, FPR, overhead (median added latency and tokens versus baseline), per model/defense/channel/source.
- Wilson confidence intervals for proportions.
- Treat repeats correctly: compute per-case rates first, then aggregate over cases, and state the unit of analysis.
- A comparison table versus baseline (absolute point change, with intervals).
- **Security-utility frontier:** for every defense stack, plot ASR reduction against benign success, with false positive rate as marker size or a second panel. Mark the Pareto-optimal stacks (no other stack is better on both axes).
- **Policy pick (keep it small):** using your pre-set target and **dev-split rows only**, choose the least restrictive stack that meets it. Then report how that stack performs on the **test split**. If it misses the target on test, say so.
- All thresholds and rules are tuned on `dev`. Headline numbers in reports use `test`.
- Unit tests against hand-computed examples.

**Test (done when):**
- Unit tests pass, including a tiny dataset where you computed the answers by hand.
- Numbers in the summary match a manual spot check of three cells.
- A unit test on a tiny hand-made example marks the Pareto-optimal stacks correctly.
- A unit test proves the policy pick fails loudly if any test-split row is used to make the choice.

**Interview note:** Why you report intervals, and what "5 repeats of 40 attacks" can and can't tell you.

---

### C13: Full matrix run

**Goal:** The complete dataset for your results.

**Your steps:**
1. Freeze your protocol (datasets, repeats, models, defenses, thresholds) in a config file committed to Git before running. Do not tweak defenses after seeing results without recording that you did.
2. Run overnight, plugged in. Keep notes on anything odd (crashes, thermal slowdown, model updates). Do not update Ollama or re-pull models during the run, and note the Ollama version, exact model tags and digests, OS and hardware.
3. Back up the SQLite file.

**AI tasks:**
- Config for the **defense-stack study**: run each of the four defenses (hardening, rules, detector, tool guard) alone, then in combinations. All 15 non-empty combinations plus the baseline is 16 stacks, which multiplies run time. Estimate the hours from your baseline run speed first. If it is too much, run all singles, all pairs, the full stack, and a leave-one-out ablation (full stack minus each layer), and use fewer repeats for combinations (state this in the report).
- A fixed, documented order for combined defenses, since order can change results.
- Model digest and dataset hashes recorded in every run's metadata.
- Run, resume and export tools as needed.

**Test (done when):**
- The full matrix completes with an error rate you have looked at and explained.
- Summary tables exist per model and defense.
- An ablation table shows how much each layer adds or removes when combined with the others.
- A smaller human audit (20-30 runs) of defended runs agrees with the scorer.

**Interview note:** Be ready to explain every number, including the disappointing ones.

---

### C14: Adaptive round

**Goal:** Test whether your best defenses survive attacks written to beat them.

**Your steps (mostly yours):**
1. Pick your strongest 1-2 defenses. Study how each one decides to block (rules, threshold, allow-list).
2. Write 15-30 new attack cases designed to get past exactly those defenses, against your own mock apps only. Organize them with this small taxonomy and tag each case with its `technique` (aim for 3-5 per technique):
   - **paraphrase:** the same intent in different wording
   - **encoding:** the instruction transformed or obscured (different character forms, simple encodings) so pattern rules miss it
   - **split_instructions:** the instruction spread across several places in the content so no single piece looks malicious
   - **role_confusion:** content that imitates the app's own formatting or roles to look like trusted instructions
   - **tool_arg_abuse:** a call to an allowed tool but with arguments the guard should reject, aimed at gaps in the tool guard

   Add them to the separate `adaptive` split (`source: adaptive`). They must never be used to tune defenses.
3. Do two or three rounds: run, look at what got through, adjust, record what you changed. Keep the log, because the log is part of the result.
4. Do not tune your defenses on these cases afterwards and then report them as held-out. Keep adaptive cases separate from the main test set.

**AI tasks:**
- Support for the `adaptive` source and round numbers in the data and reports.
- A before/after table per defense: ASR on standard attacks versus on adaptive attacks.
- A breakdown by `technique`, showing which technique beats which defense.

**Test (done when):**
- Adaptive cases validate and run through the full pipeline.
- The before/after table exists and is reported honestly, whatever it shows.
- Every adaptive case has a technique tag, and none of them appear in the dev or test splits.

**Interview note:** This is your strongest talking point: "defense X looked good at Y%, and under adaptive attack it dropped to Z%."

---

### C15: Report generation

**Goal:** One command that turns results into a readable report.

**Your steps:**
- Decide the 4-5 questions the report must answer, for example "Which defense lowers ASR most?", "What does it cost in benign success?", "Which attack type is hardest to stop?", "What happened under adaptive attack?".

**AI tasks:**
- `injectlab report results.db --out report.html`.
- Tables and charts: ASR by defense and model (with intervals), ASR vs benign success trade-off scatter, FPR by defense, overhead by defense, direct vs indirect breakdown, adaptive before/after.
- A "limitations" section generated from facts (model sizes tested, repeats, dataset sizes, which detector training data may overlap).
- Export tables to Markdown/CSV for the README.

**Test (done when):**
- Report opens in a browser, and three numbers match the raw database.
- Empty or partial results show helpful messages and do not crash.

**Interview note:** Be ready to justify each chart: what decision it supports.

---

### C16: Packaging, CI, docs, write-up

**Goal:** Something a stranger can run, extend and evaluate in under an hour.

**Your steps:**
1. Follow your own README on a clean machine or a fresh virtual environment, as a stranger would. Fix every place you get stuck.
2. Add 3-5 "good first issue" tickets (for example "add a defense", "add an attack set").
3. Write `docs/REPORT.md`: problem, method, datasets and licenses, defenses, results, adaptive round, limitations, future work.
4. Record a 2-minute demo video: run a config, open the report, explain the main finding.
5. Put the headline results table at the top of the README.

**AI tasks:**
- README with a 5-minute quickstart (install, pull a model, run one command, open the report).
- `CONTRIBUTING.md` explaining the plugin points: attack sets (drop a JSONL file), defenses (subclass `Defense`), targets (adapter), scorers.
- GitHub Actions: lint, unit tests and a **fake-model smoke test** that runs the whole pipeline end to end with no LLM.
- Dockerfile, LICENSE, version tag, example configs.
- **Reproducibility package:** a `repro/` folder with the frozen config, seeds, exact model identifiers and digests, Ollama version, dataset files and hashes, the raw SQLite database from your reported run, the human-audit file, and one command (for example `injectlab repro`) that re-runs a small slice and regenerates the full report from the saved database. State plainly that re-running LLM calls may give slightly different outputs even with fixed seeds, while regenerating the report from the saved database is exactly reproducible.
- A "responsible use" section: mock tools only, test your own apps, no real-world targets.

**Test (done when):**
- Fresh clone, follow the README: you reach a report in under an hour.
- CI is green including the smoke test.
- README numbers match the exported results.
- Regenerating the report from the saved database reproduces the published tables exactly.

---

## 8. Handoff prompt template (copy for each component)

Paste this to your AI assistant when starting a component:

```
Read INJECTLAB_PROJECT_GUIDE.md. We are now working on component C__ only.
Follow the rules in section 0.
1. Restate the goal and list the files you will create or change.
2. Build only that component.
3. Give me the exact commands to run it and the test steps from the guide.
4. Stop and wait for me to report test results. Do not start the next component.
```

When a test fails, paste:

```
Component C__ failed this test: <test>. Here is the error / what I saw: <details>.
Fix only this problem without changing finished components, and explain the cause in 2-3 lines.
```

---

## 9. Interview preparation checklist (for you)

Be able to answer these without notes:

- What problem does InjectLab address, in 20 seconds?
- What is the difference between direct and indirect injection?
- Why score with a canary and mock tools instead of an LLM judge? What does that miss?
- Why run each case several times? What does a confidence interval tell you here?
- Which defense helped most, and what did it cost in benign success?
- Why did you measure false positives? Show a case where a defense hurt normal use.
- What happened in the adaptive round? How did you avoid tuning defenses on the same cases you report?
- What can a small local model tell you, and what can't it?
- Why not just use garak or promptfoo? (They scan generically; you measured specific defenses on your own apps with utility cost and an adaptive round.)
- How can someone else add a defense or an attack set?
- What are the limits: datasets, languages, model sizes, detector training overlap?
- What is the security-utility frontier, and which stacks sit on it?
- How did you split dev and test, and why does that matter?
- How well did your scorer agree with a human, and what did the disagreements look like?
- Which adaptive technique beat which defense?
- What can someone reproduce exactly, and what can't be reproduced because LLM output varies?

**Resume bullet template (fill in real numbers only):**
- Built InjectLab, an open-source harness measuring prompt-injection defenses on local LLMs, with programmatic scoring (canary and mock tools), repeated runs and confidence intervals.
- Compared N defense layers on M models: best combination cut attack success from X% to Y% at a Z-point benign-success cost; an adaptive round raised it back to W%.

---

## 10. Time plan (about 8 weeks, flexible)

| Weeks | Components |
|---|---|
| 1 | C0, C1, C2 |
| 2 | C3, C4, C5 (start reading datasets and writing your own cases in week 1) |
| 3 | C6, C7 |
| 4 | C8, C9, C10 |
| 5 | C11, C12 |
| 6 | C13 (defense-stack study) |
| 7 | C14 (adaptive round) |
| 8 | C15, C16, buffer |

**If you fall behind:** use 2 defense layers instead of 4, one victim app instead of two, and one model instead of two. If the defense-stack study is too big, run singles, the full stack and the leave-one-out ablation only, and drop the policy pick before dropping anything else. Do not drop the benign-success measurement, the confidence intervals, the dev/test split, the human audit or the adaptive round, because those are what make the project credible.

---

## 11. Combining with the LLM Gateway (optional)

If you also build the LLM Gateway, InjectLab can become its evaluation: run the same attack and benign sets through the gateway with its guardrails switched on and off, and report the difference. Keep the two projects as separate repos or clearly separate packages so each stays explainable.
