# EMBER2024 APK — threshold operating-point analysis

**Run date:** 25 November 2026
**Status:** PASS — threshold sweep, confusion-count validation, model reload/inference and artifact upload
**Repository commit:** a9a13040fcb6f681ea518c38c1b320d41d9dae16
**CI run:** [45610953972 — CI](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45610953972)
**Benchmark run:** [45611105143 — EMBER2024 APK benchmark](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45611105143)

## Scope

This report evaluates the operating-point trade-offs of the existing HistGradientBoostingClassifier on the same deterministic temporal test sample used by the bounded EMBER2024 APK baseline. It computes the confusion matrix and derived rates at explicit probability thresholds from 0.1 to 0.9.

The decision rule is **predict malicious when predict_proba for the malicious class is greater than or equal to the threshold**. The positive class is malicious.

This is a descriptive threshold sweep on the held-out test sample. It is **not** a formal probability-calibration experiment and it must not be used to select a production threshold. A production candidate must first be chosen using a separate validation split, then evaluated once on a later untouched test split.

## Dataset and source coverage

| Item | Verified value |
|---|---|
| Dataset | EMBER2024 APK static features |
| Dataset repository | joyce8/EMBER2024 |
| Dataset revision | 3d23efef7c0f0b702c5024400cfff4c3744a3832 |
| Declared license | Apache-2.0 (as declared by upstream repository and dataset card) |
| Feature extractor | FutureComputing4AI/EMBER2024 |
| Extractor revision | 0ef753e81d98bf209f71b03cd331dfc190b5b54d |
| Feature function | PEFeatureExtractor.process_raw_features |
| Feature width / dtype | 2,568 / float32 |
| Sampling | Deterministic reservoir within each upstream temporal split |
| Sampling seed | 42 |
| Train sample | 10,000 rows |
| Test sample | 2,000 rows |
| Test benign / malicious | 998 / 1,002 |

The benchmark scanned every source JSONL line before selecting the bounded sample:

| Split | Files | Source rows scanned | Unique labeled hashes | Duplicate rows skipped | Exported sample | Scan cap reached |
|---|---:|---:|---:|---:|---:|---|
| Train | 52 | 416,000 | 208,000 | 208,000 | 10,000 | No |
| Test | 12 | 96,000 | 48,000 | 48,000 | 2,000 | No |

The sampled train/test SHA-256 overlap was **0**. This audit covers the selected sample only; it does not assert that all unique rows in the full source corpus were exhaustively cross-compared across splits.

## Threshold sweep

All values below are calculated on the same **2,000-row** held-out test sample. Percentages are rounded to two decimal places. TP = true positive, FP = false positive, TN = true negative, FN = false negative.

| Threshold | TP | FP | TN | FN | Accuracy | Precision | Recall | Specificity | F1 | FPR | FNR |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.1 | 969 | 305 | 693 | 33 | 83.10% | 76.06% | 96.71% | 69.44% | 85.15% | 30.56% | 3.29% |
| 0.2 | 939 | 197 | 801 | 63 | 87.00% | 82.66% | 93.71% | 80.26% | 87.84% | 19.74% | 6.29% |
| 0.3 | 916 | 148 | 850 | 86 | 88.30% | 86.09% | 91.42% | 85.17% | 88.67% | 14.83% | 8.58% |
| 0.4 | 888 | 114 | 884 | 114 | 88.60% | 88.62% | 88.62% | 88.58% | 88.62% | 11.42% | 11.38% |
| 0.5 | 858 | 89 | 909 | 144 | 88.35% | 90.60% | 85.63% | 91.08% | 88.05% | 8.92% | 14.37% |
| 0.6 | 819 | 70 | 928 | 183 | 87.35% | 92.13% | 81.74% | 92.99% | 86.62% | 7.01% | 18.26% |
| 0.7 | 761 | 49 | 949 | 241 | 85.50% | 93.95% | 75.95% | 95.09% | 84.00% | 4.91% | 24.05% |
| 0.8 | 698 | 30 | 968 | 304 | 83.30% | 95.88% | 69.66% | 96.99% | 80.69% | 3.01% | 30.34% |
| 0.9 | 577 | 12 | 986 | 425 | 78.15% | 97.96% | 57.58% | 98.80% | 72.53% | 1.20% | 42.42% |

Confusion counts are internally consistent at every threshold: TP + FN = 1,002 malicious records, FP + TN = 998 benign records, and TP + FP + TN + FN = 2,000 total test rows.

## Interpretation

- At threshold **0.1**, recall is **96.71%** (FNR **3.29%**), but FPR is **30.56%**: 305 of 998 benign samples are flagged.
- At threshold **0.9**, FPR falls to **1.20%**, but FNR rises to **42.42%**: 425 of 1,002 malicious samples are missed.
- At threshold **0.5**, the confusion matrix is TP **858**, FP **89**, TN **909**, FN **144**. Its FPR is **8.92%** and FNR is **14.37%**; these values reproduce the baseline precision (**90.60%**) and recall (**85.63%**).
- The largest observed F1 in this sweep is **88.67%** at threshold **0.3**; the largest observed accuracy is **88.60%** at threshold **0.4**.

Those last two observations are descriptive sample results only. They are **not** a recommendation to use either threshold in production: choosing the threshold that maximizes a metric on this same test set would overfit the evaluation set.

## Baseline model validation

The training metrics remained:

| Metric | Result |
|---|---:|
| Accuracy | 88.35% |
| Precision | 90.60% |
| Recall | 85.63% |
| F1 | 88.05% |
| ROC-AUC | 95.35% |

The saved model was reloaded and inference was run on 16 held-out APK feature rows: **PASS**. Model file size: 1,844,636 bytes. SHA-256: e77e7c1ce154de5f5095ecbcdbca1e0287ea047e55c40b26a89fe6ca36519ad6.

## CI, artifact and reproducibility

- CI 45610953972: **PASS** — Ruff lint, Ruff format, full test job and ML integration smoke test.
- Benchmark run 45611105143: **PASS** — source import/count/export, split audit, training, threshold checks, model reload/inference, provenance and artifact upload.
- Artifact name: ember2024-apk-baseline-45611105143
- Artifact ID: 15020775663
- Artifact size: 815,471 bytes
- Artifact SHA-256: d57213ffa42de26500899113f46bc83f07dfd5891326abf931f4c0b6e7abfd20
- Artifact expiry: **9 December 2026, 12:14:38 UTC**
- [Open benchmark run and download artifact](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45611105143)

The artifact contains the model, metrics, import/export reports, split audit, threshold analysis and provenance manifest. Verification of its file list found no .jsonl, .csv or .dat dataset files. No executable malware samples were downloaded or run.

## Limitations and next steps

1. Create a separate validation split for threshold selection; use a later untouched test set for the final reported performance.
2. Run multiple reservoir seeds and report metric dispersion and threshold stability.
3. Perform formal probability calibration analysis (for example, reliability curves and Brier score) on validation data; the present threshold sweep is not calibration.
4. Evaluate an independent, later or separately sourced APK dataset to measure temporal and source generalization.
5. Test Android inference cost (latency, RAM, package size and battery impact) before any endpoint integration.

This is still a bounded static-feature research baseline, not a live protection service or production-ready malware verdict engine. No endpoint deployment or automatic file action was performed.
