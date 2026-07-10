---
id: OUTPUT-REPORT
title: Results Report — Cross-domain Generalization Tests
version: 1.0
status: Active
date: 2026-07-10
author: Prof. Marx A. García Delgado
---

# Results Report — Cross-domain Generalization Tests

This document explains, in plain language, what the three HTML
dashboards generated during Milestone 1's generalization tests show,
and serves as a guide for anyone who wants to reproduce these tests
with their own Kaggle datasets.

---

## Part 1 — The three runs, explained

### Test 1 — Tirendaz / Yasserh (Milestone 1 baseline)

**Dataset:** `yasserh/twitter-tweets-sentiment-dataset` — 27,481 labeled
tweets, domain: Twitter, short text.

**Result:** ✅ full success, `warnings=[]` — no unusual data detected.

**What the dashboard shows:** balanced sentiment distribution across
the three categories (positive, negative, neutral), per-row engagement
computed with no errors, and correctly grouped languages (mostly
English, with an "other" group for minority languages). This is the
reference behavior the other two runs are compared against.

---

### Test 2 — IMDb 50K Movie Reviews

**Dataset:** `ibrahimqasimi/imdb-50k-cleaned-movie-reviews` — 50,000
movie reviews, domain: long-form text (hundreds of words per row),
completely different from Twitter.

**Result:** ✅ full success, `warnings=[]`.

**Real finding — inference time scales with text length.** The
`0008-sentiment-analyzer` skill took **18 minutes 34 seconds**
processing IMDb's reviews, versus **16 seconds** processing Tirendaz's
tweets in the baseline run — roughly **70x slower**. This isn't a bug:
it reflects RoBERTa's real token-by-token processing cost on long text,
versus ~280-character tweets. **Practical implication:** anyone
applying SIGMA to long-form domains (reviews, articles, transcripts)
should expect proportionally longer `0008` runtimes, and may need to
tune `batch_size` in `defaults.yaml`.

**What it demonstrates:** the pipeline correctly generalizes to a
completely different text domain from the original one, with no code
changes — only by adjusting the `SIGMA_INGESTION_REQUIRED_COLUMN`
variable (see Part 2 of this document).

---

### Test 3 — Social Media Sentiment 2026

**Dataset:** `algozee/social-media` — 2,200 rows combining Twitter,
Reddit, and YouTube.

**Result:** ✅ success with warnings — the pipeline paused once for
human approval (HITL), resumed manually due to the ongoing Zulip bot
deactivation (see "Known limitations" in the README).

**Real finding — the original dataset only contains 10 unique texts.**
Verified directly against the CSV: of 2,200 rows, only 10 distinct
`post_text` values exist, each repeated between 199 and 243 times.
`0002-data-cleanser` correctly detected this massive duplication and
reported it (`warnings: ['high_duplicate_rate']`) instead of silently
processing redundant data — correct behavior, not a deduplicator failure.

**Real finding — the automatic HITL trigger worked as designed.** With
only 10 rows remaining after deduplication, 40% of classifications came
back `UNCLEAR` (above ADR-004's 30% threshold), and the pipeline
automatically paused requesting human confirmation before continuing —
exactly the behavior ADR-004 and ADR-008 (K⊆X) require under high uncertainty.

**What it demonstrates:** this run is less useful as "domain
generalization" evidence (due to the source dataset's extreme
duplication) and more useful as evidence that **the quality and human
approval mechanism works correctly on ambiguous data**. A stronger
social-media generalization test would need a dataset with genuinely
unique text per row.

---

## Comparison summary

| Dataset | Domain | Result | Evidence it provides |
|---|---|---|---|
| Tirendaz (Yasserh) | Twitter, short text | ✅ success, warnings=[] | Verified baseline behavior for Milestone 1 |
| IMDb 50K | Movie reviews, long text | ✅ success, warnings=[] | Real domain generalization; inference cost scales with text length |
| Social Media 2026 | Multi-platform | ✅ success_with_warnings | Correct behavior of the HITL trigger and duplicate detection; doesn't provide generalization evidence due to the source dataset's low text uniqueness |

---

### Local vs. MinIO dashboard persistence — by submode

| Submode | Where the dashboard lands |
|---|---|
| `Dev` | Local file: `outputs/dashboards/{trace_id}/index.html` |
| `Full` | MinIO only: `minio://dashboards/{trace_id}/index.html` — never written to local disk. Download it manually via the MinIO web console (`http://localhost:9003`, `dashboards` bucket) if you need a local copy. |

This is why, of the 6 runs documented in this report, only the quick
Dev-mode test automatically generated a folder inside
`outputs/dashboards/` — runs 3 through 6 (all in Full mode) were
downloaded manually from MinIO and renamed for this report.

---

## Navigation — HTML dashboards for every run

| # | File | Dataset | Result |
|---|---|---|---|
| 1 | [dashboard_run1_failed.html](dashboard_run1_failed.html) | Tirendaz (Yasserh) | ❌ Failed — see `TROUBLESHOOTING.md` |
| 2 | [dashboard_run2_failed.html](dashboard_run2_failed.html) | Tirendaz (Yasserh) | ❌ Failed — see `TROUBLESHOOTING.md` |
| 3 | [dashboard_run3_ok.html](dashboard_run3_ok.html) | Tirendaz (Yasserh) | ✅ Success, pre-`sigma/` restructuring |
| 4 | [dashboard_run4_ok.html](dashboard_run4_ok.html) | Tirendaz (Yasserh) | ✅ Success, post-restructuring, `warnings=[]` |
| 5 | [dashboard_run5_imdb_ok.html](dashboard_run5_imdb_ok.html) | IMDb 50K Reviews | ✅ Success, `warnings=[]` — see Test 2 above |
| 6 | [dashboard_run6_social_ok_warnings.html](dashboard_run6_social_ok_warnings.html) | Social Media 2026 | ✅ Success with warnings — see Test 3 above |

> **Note:** if you're looking for `test_dashboard_fix.html`, that file
> is **not** a pipeline run — it's the output of a one-off verification
> of `0011-viz-reporter`'s rendering fix (see `TROUBLESHOOTING.md`). It
> lives alongside its script at
> [`tests/test_dashboard_fix.html`](../tests/test_dashboard_fix.html),
> not in this folder.

Detailed analysis of runs 5 and 6 (the cross-domain generalization
tests) is in Part 1 of this document. Runs 1-4 document Milestone 1's
evolution on the baseline dataset (two diagnosed-and-fixed failures,
then two successes before and after the code restructuring into `sigma/`).

---

## Part 2 — How to reproduce these tests with your own Kaggle dataset

### Step 1 — Create an account and get your API token

1. Create a free account at [kaggle.com](https://www.kaggle.com).
2. Go to your profile → **Settings** → **API** section → **Create New Token**.
3. This downloads `kaggle.json` with your credentials.
4. Place it at `C:\Users\<your_user>\.kaggle\kaggle.json` (Windows).

### Step 2 — Search datasets from the terminal

```cmd
kaggle datasets list -s "your topic of interest" --sort-by hottest
```

Prioritize datasets with a `usabilityRating` close to 1.0 — Kaggle's own
quality metric.

### Step 3 — Download and verify structure before running the pipeline

```cmd
kaggle datasets download <user>/<slug> -p data\raw\test_name --unzip
python -c "import pandas as pd; df = pd.read_csv('data/raw/test_name/file.csv'); print(df.columns.tolist())"
```

**Never assume the column name** — always verify it before running the
full pipeline, exactly as was done for this report.

### Step 4 — Adjust the text column name (no code changes needed)

```cmd
set SIGMA_INGESTION_REQUIRED_COLUMN=your_real_column_name
python orchestrator.py --variant Full --data-path ./data/raw/test_name/file.csv
```

---

## Part 3 — Candidate datasets for future tests (reviewed catalog)

Obtained via a real `kaggle datasets list` call (not listed from
memory), across two searches: `"twitter sentiment"` and `"sentiment
analysis nlp"`, both sorted by popularity (`--sort-by hottest`).

| Dataset | Domain | Size | usabilityRating | Status |
|---|---|---|---|---|
| `yasserh/twitter-tweets-sentiment-dataset` | Twitter | 1.3 MB | 1.0 | ✅ Reviewed and used (baseline) |
| `ibrahimqasimi/imdb-50k-cleaned-movie-reviews` | Movie reviews | 3.7 MB | 1.0 | ✅ Reviewed and tested |
| `algozee/social-media` | Multi-platform | 112 KB | 1.0 | ✅ Reviewed and tested |
| `columbine/imdb-dataset-sentiment-analysis-in-csv-format` | Movie reviews | 26.9 MB | 1.0 | ⬜ Candidate — larger IMDb variant, useful for a volume test |
| `abdallahwagih/emotion-dataset` | Emotions (beyond polarity) | 218 KB | 1.0 | ⬜ Candidate — different domain: emotion classification, not binary/ternary sentiment |
| `niraliivaghani/flipkart-product-customer-reviews-dataset` | Product reviews (e-commerce) | 3.97 MB | 1.0 | ⬜ Candidate — e-commerce domain, not yet tested |
| `harshalhonde/starbucks-reviews-dataset` | Service reviews | 173 KB | 1.0 | ⬜ Candidate — customer-service domain |
| `arunavakrchakraborty/covid19-twitter-dataset` | Twitter, topic-specific | 51 MB | 1.0 | ⬜ Candidate — same domain as Tirendaz, but a distinct topic and much larger volume |
| `kazanova/sentiment140` | Twitter | 84.9 MB | 0.88 | ⬜ Candidate — the historically most popular one (275K downloads), useful for a scale test |
| `hbaflast/french-twitter-sentiment-analysis` | Twitter, French | 50.7 MB | 1.0 | ⬜ Candidate — a language-generalization test, not just domain |

**Discarded in this round, and why:** `saurabhshahane/twitter-sentiment-dataset`,
`crowdflower/twitter-airline-sentiment`,
`arkhoshghalb/twitter-sentiment-analysis-hatred-speech`, and other
Twitter datasets repeat the same domain as Tirendaz without providing
new generalization evidence. `dunyajasim/twitter-dataset-for-sentiment-analysis`
(210 MB) was discarded for its disproportionate size for a quick test.
