# LAMDA APK — training-seed stability on a fixed temporal test set

**Date:** 25 November 2026
**Repository commit:** 01c98b8c0613c333323b78d831c954b53a78ac06
**CI:** [45620239736 — PASS](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45620239736)
**Seeds:** 42, 17, 2026
**Fixed test set:** all 10,871 rows from the pinned 2023 LAMDA test split

## Purpose

This experiment measures variation caused by changing only the deterministic stratified training sample. The 2023 test split is the same full 10,871-row file in all three runs. Each run trains a separate HistGradientBoostingClassifier on 10,000 rows sampled from the same 2022 source split. It does not create three independent test sets.

This is stronger comparability than changing both train and test samples, but it is still a small seed-sensitivity experiment over one dataset. It does not establish production performance or external validity.

## Fixed data and safeguards

| Item | Value |
|---|---|
| Dataset | IQSeC-Lab/LAMDA |
| Dataset revision | d3631db3908c4bee8f9f0748f5579a9b968ec1e1 |
| 2022 source train rows | 69,132 |
| 2023 source test rows | 10,871 |
| Training sample per run | 10,000 |
| Test rows per run | 10,871 (full split) |
| Feature columns | 4,561 int8 features |
| Test benign / malicious | 9,293 / 1,578 |
| Test Parquet SHA-256 | 58f4f6356d1f88fcaeb5fa04c67a1260b4cbe736c18961dc3e51b6cd121598c2 |
| Train Parquet SHA-256 | f41b5c4f051dd5dced9adc322b221ac4fab5fa16202b07c168a80ca3d3a1662b |

Every run used identical Parquet source hashes, source labels, 2023 test rows and feature schema. Within each run, training/test SHA-256 overlap was zero; cross-split overlap removal and cross-split label conflict counts were also zero. The selected train sample remained stratified at 5,181 benign and 4,819 malicious rows in each run.

| Seed | Train benign | Train malicious |
|---:|---:|---:|
| 42 | 5,181 | 4,819 |
| 17 | 5,181 | 4,819 |
| 2026 | 5,181 | 4,819 |

The hash, family, vt_count and year_month fields were excluded from model inputs. Only the label and 4,561 int8 feature columns were used.

## Metrics by training seed

All metrics below are measured against the exact same 10,871-row test set.

| Seed | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---:|---:|---:|---:|---:|---:|
| 42 | 96.07% | 92.47% | 79.40% | 85.44% | 96.18% |
| 17 | 96.15% | 93.67% | 78.77% | 85.58% | 96.33% |
| 2026 | 96.06% | 94.30% | 77.57% | 85.12% | 96.23% |

Descriptive mean and range across the three trained models:

| Metric | Mean | Observed range | Range width |
|---|---:|---:|---:|
| Accuracy | 96.09% | 96.06%–96.15% | 0.08 percentage points |
| Precision | 93.48% | 92.47%–94.30% | 1.83 percentage points |
| Recall | 78.58% | 77.57%–79.40% | 1.84 percentage points |
| F1 | 85.38% | 85.12%–85.58% | 0.46 percentage points |
| Roc Auc | 96.25% | 96.18%–96.33% | 0.15 percentage points |

The range is not a confidence interval. The three fitted models share the same data source and fixed test set, so their results are correlated.

## Confusion matrix at threshold 0.5

Decision rule: malicious when the predicted malicious probability is greater than or equal to 0.5.

| Seed | TP | FP | TN | FN | FPR | FNR | Precision | Recall |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 42 | 1,253 | 102 | 9,191 | 325 | 1.10% | 20.60% | 92.47% | 79.40% |
| 17 | 1,243 | 84 | 9,209 | 335 | 0.90% | 21.23% | 93.67% | 78.77% |
| 2026 | 1,224 | 74 | 9,219 | 354 | 0.80% | 22.43% | 94.30% | 77.57% |

Across these seeds, false negatives ranged from 325 to 354 of 1,578 malware test samples (FNR 20.60%–22.43%). False positives ranged from 74 to 102 of 9,293 benign samples (FPR 0.80%–1.10%). The relative stability of the scores does not remove the substantial missed-malware risk.

## Mean operating-point results across seeds

Each row below is the mean across the three models; parentheses show the minimum-to-maximum range between seeds.

| Threshold | Mean precision (range) | Mean recall (range) | Mean FPR (range) | Mean FNR (range) |
|---:|---:|---:|---:|---:|
| 0.1 | 85.92% (85.04–87.12) | 83.63% (81.43–85.87) | 2.33% (2.10–2.45) | 16.37% (14.13–18.57) |
| 0.2 | 89.77% (89.08–90.53) | 81.71% (80.10–83.27) | 1.58% (1.45–1.73) | 18.29% (16.73–19.90) |
| 0.3 | 91.51% (90.06–92.30) | 80.61% (79.02–81.56) | 1.27% (1.12–1.53) | 19.39% (18.44–20.98) |
| 0.4 | 92.62% (91.50–93.20) | 79.66% (78.20–80.48) | 1.08% (0.97–1.27) | 20.34% (19.52–21.80) |
| 0.5 | 93.48% (92.47–94.30) | 78.58% (77.57–79.40) | 0.93% (0.80–1.10) | 21.42% (20.60–22.43) |
| 0.6 | 94.27% (93.42–95.01) | 77.78% (77.19–78.33) | 0.80% (0.69–0.94) | 22.22% (21.67–22.81) |
| 0.7 | 95.40% (95.02–96.01) | 76.98% (76.30–77.31) | 0.63% (0.54–0.69) | 23.02% (22.69–23.70) |
| 0.8 | 96.44% (96.15–96.73) | 75.56% (74.97–75.92) | 0.47% (0.43–0.52) | 24.44% (24.08–25.03) |
| 0.9 | 97.52% (97.25–97.69) | 73.17% (72.43–73.83) | 0.32% (0.29–0.36) | 26.83% (26.17–27.57) |

Lower thresholds increase recall but also create more false alarms. Higher thresholds reduce false alarms but increase missed malware. These operating points remain descriptive; no production threshold is selected from this repeatedly used test split.

## Workflow and artifact integrity

All three LAMDA workflows completed successfully: pinned dataset download, Parquet validation, hash filtering, deterministic sampling, model training, threshold evaluation, model reload/inference, temporary dataset cleanup, provenance generation and artifact upload.

| Seed | Workflow | Artifact ID | Artifact name | Artifact digest prefix | Model SHA-256 prefix |
|---:|---|---:|---|---|---|
| 42 | [45618793929](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45618793929) | 15023378022 | lamda-apk-cross-dataset-42 | cfb033ff8cf4ae5c… | f03808b3136aac0e… |
| 17 | [45620531676](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45620531676) | 15025300206 | lamda-apk-temporal-17 | 8cd36efafadaa908… | cfd805c934c64963… |
| 2026 | [45621037254](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45621037254) | 15025101242 | lamda-apk-temporal-2026 | e67628980ea5782e… | e898ae8b164bea9e… |

Artifacts contain the model and JSON provenance/metric reports only. Their file lists were checked to ensure no APK, Parquet, CSV, JSONL, NPZ or DAT data files were uploaded. No APK executable was downloaded or run.

## Interpretation and limitations

1. Accuracy and ROC-AUC vary little across the three training samples. Precision, recall and the 0.5 operating point move more noticeably.
2. This is only training-sample sensitivity on one fixed 2023 test set. It is not three independent external validations and cannot quantify dataset shift.
3. The 2023 test class distribution is imbalanced (9,293 benign, 1,578 malicious). Accuracy must be read together with recall, FNR, specificity and confusion counts.
4. LAMDA is AndroZoo-sourced and VirusTotal/AVClass2-labeled. Its provenance is not guaranteed to be independent from EMBER or other APK corpora.
5. Hash overlap between LAMDA and the earlier EMBER sample remains unverified; the complete EMBER sample hash list was not retained.
6. The LAMDA model has a 4,561-feature schema and cannot replace or validate transfer of the 2,568-feature EMBER model.

## Next defensive steps

1. Reserve a distinct validation split for threshold selection, then use a later untouched test period for a final result.
2. Add reliability curves and Brier score on validation data; the current threshold sweep is not formal probability calibration.
3. Compare against a later independent APK source with explicit cross-dataset SHA-256 overlap checks.
4. Implement a guarded inference API for validated numeric feature vectors before Android scanner integration; no arbitrary binary execution should be added.
5. Benchmark feature extraction, inference latency and RAM on Android before claiming on-device readiness.

This remains a research model assessment, not a production malware verdict engine, autonomous endpoint protection service or proof that every malware sample will be detected.
