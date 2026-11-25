# EMBER2024 APK — reservoir-seed stability check

**Date:** 25 November 2026  
**Repository commit for parameterized workflow:** 9b209100ae75bacf516df78a3231c19c998f642c  
**CI:** [45612841802 — PASS](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45612841802)  
**Scope:** three deterministic reservoir seeds (42, 17, 2026), 10,000 training rows and 2,000 temporal test rows per run.

## Purpose and interpretation

This check asks whether headline metrics and the threshold-0.5 operating point move materially when the deterministic reservoir sampling seed changes. All runs use the same pinned EMBER2024 APK source, temporal train/test split, extractor revision, model family and row caps.

This is a **sampling-sensitivity check**, not three statistically independent external validations. All samples come from the same upstream source corpus and can overlap across different seeds. The train/test SHA-256 audit is performed within each run; no claim is made that train or test samples from different seeds are mutually disjoint. Test class proportions also differ slightly by seed. These results do not establish production performance or a production threshold.

## Reproducibility controls

| Item | Value |
|---|---|
| Dataset | joyce8/EMBER2024, APK |
| Dataset revision | 3d23efef7c0f0b702c5024400cfff4c3744a3832 |
| Declared license | Apache-2.0 (as declared by upstream repository and dataset card) |
| Extractor | FutureComputing4AI/EMBER2024 / PEFeatureExtractor.process_raw_features |
| Extractor revision | 0ef753e81d98bf209f71b03cd331dfc190b5b54d |
| Feature width / dtype | 2,568 / float32 |
| Model | HistGradientBoostingClassifier |
| Training / test cap per run | 10,000 / 2,000 |
| Reservoir seeds | 42, 17, 2026 |

Each run counted and scanned all **416,000 train** and **96,000 test** JSONL source rows across 52 and 12 files before taking a bounded sample. Source scan caps remained false in all runs. Each within-run sampled train/test SHA-256 overlap was zero.

| Seed | JSONL files (train / test) | Rows scanned (train / test) | Sample exported (train / test) | Within-run train/test hash overlap | Scan cap reached |
|---:|---:|---:|---:|---:|---|
| 42 | 52 / 12 | 416,000 / 96,000 | 10,000 / 2,000 | 0 | No / No |
| 17 | 52 / 12 | 416,000 / 96,000 | 10,000 / 2,000 | 0 | No / No |
| 2026 | 52 / 12 | 416,000 / 96,000 | 10,000 / 2,000 | 0 | No / No |

## Model metrics by seed

All metrics are calculated on the corresponding 2,000-row held-out temporal test sample.

| Seed | Accuracy | Precision | Recall | F1 | ROC-AUC | FPR at 0.5 | FNR at 0.5 | Test benign | Test malicious |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 42 | 88.35% | 90.60% | 85.63% | 88.05% | 95.35% | 8.92% | 14.37% | 998 | 1002 |
| 17 | 86.85% | 87.28% | 85.58% | 86.42% | 94.46% | 11.94% | 14.42% | 1022 | 978 |
| 2026 | 88.20% | 89.76% | 85.95% | 87.81% | 95.37% | 9.59% | 14.05% | 1011 | 989 |

Descriptive mean and range across these three seed runs:

| Metric | Mean | Observed range | Range width |
|---|---:|---:|---:|
| Accuracy | 87.80% | 86.85%–88.35% | 1.50 pp |
| Precision | 89.21% | 87.28%–90.60% | 3.32 pp |
| Recall | 85.72% | 85.58%–85.95% | 0.36 pp |
| F1 | 87.43% | 86.42%–88.05% | 1.62 pp |
| Roc Auc | 95.06% | 94.46%–95.37% | 0.91 pp |

The mean/range summarize only these three sampled runs; they are not confidence intervals and do not correct for sample overlap or test-set reuse.

## Confusion matrix at threshold 0.5

Decision rule: predict malicious when the malicious-class probability is greater than or equal to 0.5. TP = true positive, FP = false positive, TN = true negative, FN = false negative.

| Seed | TP | FP | TN | FN | Accuracy | Precision | Recall | FPR | FNR |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 42 | 858 | 89 | 909 | 144 | 88.35% | 90.60% | 85.63% | 8.92% | 14.37% |
| 17 | 837 | 122 | 900 | 141 | 86.85% | 87.28% | 85.58% | 11.94% | 14.42% |
| 2026 | 850 | 97 | 914 | 139 | 88.20% | 89.76% | 85.95% | 9.59% | 14.05% |

**Observed:** recall is fairly stable across these seeds (85.58%–85.95%), while precision varies more (87.28%–90.60%). FPR at 0.5 ranges from 8.92% to 11.94%; FNR ranges from 14.05% to 14.42%. In these three runs, false-positive behavior varies more than false-negative behavior. Three samples are too few to establish a general property.

The best-F1 threshold also varied: seed 42 = 0.3; seed 17 = 0.3; seed 2026 = 0.4. These are descriptive maxima on the same test samples; they are **not threshold recommendations**.

## Model and artifact integrity

All three workflows completed successfully, including source import/count/export, label and split audit, training, threshold sweep, model reload/inference, provenance manifest and artifact upload. Reload and inference on 16 held-out APK rows passed in every run.

| Seed | Workflow run | Artifact ID | Artifact SHA-256 (prefix) | Model SHA-256 (prefix) |
|---:|---|---:|---|---|
| 42 | [45611105143](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45611105143) | 15020775663 | d57213ffa42de265… | e77e7c1ce154de5f… |
| 17 | [45613002750](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45613002750) | 15020189038 | 0ca5aa55d12b2e7b… | aec9ff761f36a8b9… |
| 2026 | [45613448461](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45613448461) | 15020798476 | 13251669a8641001… | 40a553875a3a18ed… |

Each artifact contains the model, metrics, JSON provenance and split/export audit only. Downloaded artifact file lists were checked: no .jsonl, .csv or .dat source/feature dataset files were included. No executable malware samples were downloaded or executed.

## Conclusions and next actions

1. Core detection metrics remain in a relatively narrow band across these three samples: accuracy 86.85%–88.35%, recall 85.58%–85.95%, and ROC-AUC 94.46%–95.37%.
2. Precision (87.28%–90.60%) and FPR at threshold 0.5 (8.92%–11.94%) move more visibly. A single seed-42 result therefore understates uncertainty in false-alarm behavior.
3. Threshold-0.5 FNR ranges from 14.05% to 14.42%, so this sample check does not remove the risk of missed malware.
4. Create a separate validation split for threshold selection; preserve a later untouched temporal test period for one final evaluation.
5. Add a formally separate calibration assessment (reliability curve and Brier score), test an independent later APK collection, and benchmark Android inference resource use.

This remains a bounded static-feature research baseline, not a live protection service or production-ready verdict engine. No endpoint deployment or automatic file action was performed.
