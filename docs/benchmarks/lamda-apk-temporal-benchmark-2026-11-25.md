# LAMDA APK temporal benchmark — 2022 train / 2023 test

**Benchmark date:** 25 November 2026
**Repository commit evaluated:** 024d7fb680a1aad6515ccf9e33e255d39d76d42e
**CI:** [45618495262 — PASS](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45618495262)
**LAMDA benchmark:** [45618793929 — PASS](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45618793929)

## Scope and important interpretation

This is a separately trained LAMDA temporal benchmark. It trains a new HistGradientBoostingClassifier on a bounded sample from LAMDA's 2022 training split and evaluates it on the 2023 test split. It is not a transfer evaluation of the EMBER2024 model on LAMDA: EMBER uses 2,568 features, whereas LAMDA uses 4,561 int8 features. The two models are not interchangeable.

The benchmark uses pre-extracted feature Parquet files only. It does not download or execute original APK files.

## Dataset provenance and integrity

| Item | Verified value |
|---|---|
| Dataset | IQSeC-Lab/LAMDA |
| Pinned revision | d3631db3908c4bee8f9f0748f5579a9b968ec1e1 |
| Declared license | MIT (as stated by the upstream dataset card) |
| Original APK source | AndroZoo |
| Label provenance | VirusTotal vendor detections; malware label at 4 or more detections; AVClass2 family metadata |
| Train source file | Baseline/2022/2022_train.parquet |
| Test source file | Baseline/2023/2023_test.parquet |
| Train Parquet SHA-256 | f41b5c4f051dd5dced9adc322b221ac4fab5fa16202b07c168a80ca3d3a1662b |
| Test Parquet SHA-256 | 58f4f6356d1f88fcaeb5fa04c67a1260b4cbe736c18961dc3e51b6cd121598c2 |
| Feature schema | 4,561 int8 columns: feat_0 through feat_4560 |

Source and sample counts:

| Split | Source rows | Benign | Malicious | Model rows |
|---|---:|---:|---:|---:|
| 2022 train source | 69,132 | 35,814 | 33,318 | — |
| Stratified 2022 train sample | — | 5,181 | 4,819 | 10,000 |
| 2023 test source and evaluation | 10,871 | 9,293 | 1,578 | 10,871 |

The test split was evaluated in full; its size was below the workflow's 12,000-row maximum. The train sample used deterministic stratified sampling with seed 42.

The preparer validated the required schema, binary labels and SHA-256 values. It found:
- Cross-split SHA-256 overlap removed from train: 0
- Cross-split label conflicts: 0
- SHA-256 overlap between the selected train and test samples: 0

The hash, family, vt_count and year_month columns were excluded from model input. Only the label target and 4,561 feature columns were used.

## Held-out test metrics

The model's default operating point is threshold 0.5:

| Metric | Result |
|---|---:|
| Accuracy | 96.07% |
| Precision | 92.47% |
| Recall / sensitivity | 79.40% |
| Specificity | 98.90% |
| F1 | 85.44% |
| ROC-AUC | 96.18% |
| False-positive rate | 1.10% |
| False-negative rate | 20.60% |
| Balanced accuracy | 89.15% |

The test set is imbalanced: 9,293 benign samples versus 1,578 malicious samples. Accuracy alone therefore overstates the practical picture. At threshold 0.5 the detector missed 325 of 1,578 malicious samples (FNR 20.60%) and incorrectly flagged 102 of 9,293 benign samples (FPR 1.10%).

## Threshold operating-point sweep

Decision rule: classify as malicious when the malicious-class probability is greater than or equal to the threshold.

| Threshold | TP | FP | TN | FN | Precision | Recall | Specificity | F1 | FPR | FNR |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.1 | 1,355 | 228 | 9,065 | 223 | 85.60% | 85.87% | 97.55% | 85.73% | 2.45% | 14.13% |
| 0.2 | 1,314 | 161 | 9,132 | 264 | 89.08% | 83.27% | 98.27% | 86.08% | 1.73% | 16.73% |
| 0.3 | 1,287 | 142 | 9,151 | 291 | 90.06% | 81.56% | 98.47% | 85.60% | 1.53% | 18.44% |
| 0.4 | 1,270 | 118 | 9,175 | 308 | 91.50% | 80.48% | 98.73% | 85.64% | 1.27% | 19.52% |
| 0.5 | 1,253 | 102 | 9,191 | 325 | 92.47% | 79.40% | 98.90% | 85.44% | 1.10% | 20.60% |
| 0.6 | 1,236 | 87 | 9,206 | 342 | 93.42% | 78.33% | 99.06% | 85.21% | 0.94% | 21.67% |
| 0.7 | 1,220 | 64 | 9,229 | 358 | 95.02% | 77.31% | 99.31% | 85.26% | 0.69% | 22.69% |
| 0.8 | 1,196 | 44 | 9,249 | 382 | 96.45% | 75.79% | 99.53% | 84.88% | 0.47% | 24.21% |
| 0.9 | 1,156 | 28 | 9,265 | 422 | 97.64% | 73.26% | 99.70% | 83.71% | 0.30% | 26.74% |

The lower threshold catches more malware but creates more false alarms. At threshold 0.1, 223 malicious samples were missed and 228 benign samples were flagged. At threshold 0.9, benign false alarms fell to 28, but 422 malicious samples were missed.

The maximum observed F1 in this sweep was 86.08% at 0.2; the maximum observed accuracy was 96.12% at 0.7. These are descriptive maxima on this same test split, not production threshold recommendations. Selecting a production threshold requires a separate validation split and a later untouched test set.

## Model reload and artifact verification

- Model reload and inference on 16 held-out feature rows: PASS
- Test rows available to inference pipeline: 10,871
- Feature count: 4,561
- Predicted classes among the 16-row smoke batch: 15 benign / 1 malicious
- Probability range for that smoke batch: 0.0001758–0.9203758
- Model file size: 797,771 bytes
- Model SHA-256: f03808b3136aac0e31d27c08244925f35f7fa8e189784ad6c1f73fbf3292f8e2

GitHub artifact:
- Name: lamda-apk-cross-dataset-42
- Artifact ID: 15023378022
- Archive size: 178,274 bytes
- Archive digest: sha256:cfb033ff8cf4ae5c70067dea8e8713cf6001bd636ef0ed916d7927f500c00a67
- Expires: 9 December 2026, 12:59:41 UTC
- [Open benchmark run and artifact](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45618793929)

The uploaded artifact contains only the model and JSON reports/manifests. It contains no .apk, .parquet, .csv, .jsonl, .npz or .dat files. The Parquet files and generated CSVs were removed from the hosted runner before artifact creation.

## What this proves — and what it does not

**Proven:** the bounded 2022-to-2023 LAMDA preparation, hash filtering, training, threshold sweep, model reload and metadata-only artifact workflow completed successfully.

**Not proven:**
1. This does not establish that the EMBER model generalizes to LAMDA; a separate LAMDA model was trained.
2. Cross-dataset APK hash overlap with the earlier EMBER sample has not been verified because the full EMBER sample hash list was not retained.
3. LAMDA is AndroZoo-sourced and VirusTotal/AVClass2-labeled; it is not guaranteed to be provenance-independent from all other APK corpora.
4. A single seed-42 LAMDA run is not a stability or production validation.
5. No live APK scanner/API inference endpoint or Android on-device inference integration was validated by this benchmark.
6. The 20.60% FNR at threshold 0.5 means a material number of malicious test samples were missed.

## Next defensive steps

1. Repeat the LAMDA benchmark with at least two additional deterministic seeds and compare metric dispersion.
2. Retain a distinct validation split for threshold selection; reserve a later untouched test set for final evaluation.
3. Add formal probability-calibration assessment (reliability curve and Brier score) on validation data.
4. Build a guarded inference API accepting validated numeric feature vectors only, with explicit schema/version, model hash, threshold metadata and no arbitrary file execution.
5. Validate static feature extraction and inference latency/RAM on Android before scanner integration.
6. Add safe incident-response agent orchestration only after model inference and tool permissions are testable; keep MCP tools read-only or tightly scoped.

This remains a research classifier, not a production malware verdict engine or an autonomous endpoint protection product. No endpoint deployment, malicious payload generation or execution was performed.
