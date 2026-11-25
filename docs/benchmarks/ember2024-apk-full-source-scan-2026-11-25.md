# EMBER2024 APK — full-source-scan baseline

**Run date:** 25 November 2026
**Status:** PASS — full JSONL source scan, split audit, training, model reload/inference and artifact upload
**Repository commit:** `1338364a321ab1d87dc6c5af13e7db388a852337`
**GitHub Actions run:** [45599816585 — EMBER2024 APK baseline](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45599816585)
**CI run for the same commit:** [45599618519 — CI](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45599618519)

## Scope and provenance

This is a bounded-row model baseline made after scanning every extracted APK train/test JSONL record. It is **not** a model trained on every unique source record.

| Item | Verified value |
|---|---:|
| Dataset | EMBER2024 APK static features |
| Hugging Face repository | `joyce8/EMBER2024` |
| Dataset revision | `3d23efef7c0f0b702c5024400cfff4c3744a3832` |
| Declared dataset license | Apache-2.0 |
| Feature extractor | `FutureComputing4AI/EMBER2024` / `thrember` |
| Extractor revision | `0ef753e81d98bf209f71b03cd331dfc190b5b54d` |
| Feature implementation | `PEFeatureExtractor.process_raw_features` |
| Feature columns | 2,568 float32 values |
| Signify compatibility pin | `signify==0.8.1` |

The train archive contained 52 weekly JSONL files from **24 September 2023 through 21 September 2024** (2,121,631,676 extracted bytes). The temporal test archive contained 12 weekly JSONL files from **22 September 2024 through 14 December 2024** (483,247,854 extracted bytes). The workflow records each extracted JSONL member's SHA-256 in the provenance manifest.

Only pre-extracted feature/label JSONL was imported. No original executable malware samples were downloaded or executed.

## Source completeness and deduplication

The workflow counts the lines in every extracted train/test JSONL file before feature extraction. It then passes those exact counts to the streaming exporter and checks both the scanned row count and processed JSONL file count. The exporter also reports whether it encountered an additional source row after the cap.

| Source split | JSONL files | Source rows counted | Rows scanned | Unique labeled SHA-256 records | Exact duplicates skipped | Unlabeled skipped | Scan cap reached |
|---|---:|---:|---:|---:|---:|---:|---|
| Train | 52 | 416,000 | 416,000 | 208,000 | 208,000 | 0 | No |
| Test | 12 | 96,000 | 96,000 | 48,000 | 48,000 | 0 | No |

**Completeness result:** all 512,000 source rows across all 64 JSONL files were scanned. The workflow verified the per-split row totals, file counts and `source_scan_cap_reached=false` for both splits.

## Sampling and split audit

The exporter used deterministic Algorithm-R reservoir sampling with seed **42**, independently inside the existing temporal train and test splits. This prevents the model from being trained on an early prefix while preserving the upstream time separation.

| Sample | Unique rows selected | Benign (0) | Malicious (1) |
|---|---:|---:|---:|
| Train | 10,000 | 4,980 | 5,020 |
| Test | 2,000 | 998 | 1,002 |

The sampled train and test SHA-256 sets had **zero overlap**. This is an audit of the selected model sample; it is not a claim that every cross-split record in the complete upstream dataset was independently pairwise compared.

## Model and metrics

Model: `HistGradientBoostingClassifier`, using the repository's static-feature training pipeline.

| Metric | Result |
|---|---:|
| Accuracy | **88.35%** |
| Precision | **90.60%** |
| Recall | **85.63%** |
| F1 | **88.05%** |
| ROC-AUC | **95.35%** |

These metrics apply to the deterministic 10,000/2,000 sampled rows, not all 208,000/48,000 unique labeled records. They are a baseline, not a production performance guarantee.

## Model artifact validation

The workflow reloaded the saved `.joblib` model, checked its dataset ID and 2,568-feature schema, then performed inference on 16 held-out APK test-feature rows.

- Reload and inference: **PASS**
- Inference rows: 16
- Predictions: 11 benign / 5 malicious
- Predicted probability range: 0.00123–0.99420
- Model file: `static-malware-detector-v1.joblib`
- Model size: 1,844,636 bytes
- Model SHA-256: `e77e7c1ce154de5f5095ecbcdbca1e0287ea047e55c40b26a89fe6ca36519ad6`

The verified model was downloaded to the device at:

```text
~/ember-baseline-verified/models/static-malware-detector-v1.joblib
```

## Reproducibility and artifact

The workflow run uses the repository commit and pinned dataset/extractor revisions listed above. It stores the model, metrics, split audit, feature-export reports, model-validation report and manifest in this GitHub Actions artifact:

- Artifact name: `ember2024-apk-baseline-45599816585`
- Artifact ID: `15014243968`
- Artifact SHA-256: `61c87fb821201e8cb15c5f3f9c7f47e3c7de863712d042e11e220bbb68ec610f`
- Retention expiry: **9 December 2026, 11:00:31 UTC**
- [Open workflow run and download artifact](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45599816585)

The artifact does not contain the original dataset, raw JSONL metadata or exported feature CSVs. The job removes raw JSONL and vector files from its temporary runner workspace before training/artifact upload.

## Limitations and next research steps

1. Increase the selected training and test sample sizes, or evaluate all unique labeled records on a runner sized for that experiment.
2. Repeat with multiple fixed seeds and report metric variance; seed 42 provides reproducibility, not uncertainty estimates.
3. Select a candidate threshold using a separate validation split; the descriptive held-out test threshold sweep is recorded in [the threshold analysis report](ember2024-apk-threshold-analysis-2026-11-25.md).
4. Compare with a simple baseline and a second model family before considering deployment.
5. Keep temporal separation and the SHA-256 leakage checks in every future evaluation.

The detector is a static-feature classifier. A prediction is not proof of malicious intent or execution, and this benchmark did not deploy the model to endpoints.
