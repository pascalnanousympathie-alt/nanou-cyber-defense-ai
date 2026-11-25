# Defensive datasets

This directory contains manifests and import guidance only. Large datasets are not checked into Git and no executable samples are downloaded by CI.

## EMBER2024 static features (preferred research benchmark)

EMBER2024 is a multi-format benchmark with extracted features, hashes, metadata and labels for more than 3.2 million files across Win32, Win64, .NET, APK, ELF and PDF. Its collection window is 24 September 2023 through 14 December 2024. The challenge split contains 6,315 malicious files.

- Upstream: https://github.com/FutureComputing4AI/EMBER2024
- Paper: https://arxiv.org/abs/2506.05074
- Feature data and benchmark models are hosted by the upstream project on Hugging Face.
- Approximate dataset sizes are large (for example, Win32 train 23.7 GB); choose one format/split and keep it outside this repo.
- Upstream layout: raw pre-extracted feature/label JSONL; `thrember.create_vectorized_features()` produces float32 X and int32 y `.dat` files.
- The upstream README does not clearly state a dataset license in the checked material. Verify the current license/terms before reuse or redistribution.

The importer downloads only the official feature archives and extracts flat JSONL files. It rejects traversal paths, symlinks, non-JSONL members, oversized members, suspicious compression ratios and overwrites. The vector exporter then joins sorted JSONL metadata to the corresponding .dat rows; it does not fetch, open or execute original sample files.

## EMBER 2018 static PE features (reproducible legacy baseline)

EMBER is a research benchmark containing extracted Portable Executable (PE) features and labels. It does not distribute the original executable files as part of its feature dataset. The upstream Elastic repository was archived on 13 April 2026.

- Upstream: https://github.com/elastic/ember
- Paper: H. S. Anderson and P. Roth, *EMBER: An Open Dataset for Training Static PE Malware Machine Learning Models* (2018), https://arxiv.org/abs/1804.04637
- 2018 feature archive: https://ember.elastic.co/ember_dataset_2018_2.tar.bz2
- SHA-256 from upstream README: `b6052eb8d350a49a8d5a5396fbe7d16cf42848b86ff969b77464434cf2997812`

The archive fetch helper verifies this checksum and saves to ignored `datasets/cache/`; it does not extract or execute files.

## CISA Known Exploited Vulnerabilities (KEV)

- Official catalog: https://www.cisa.gov/known-exploited-vulnerabilities-catalog
- JSON feed: https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json
- Use for vulnerability prioritization; preserve catalog version and date retrieved.

## NIST National Vulnerability Database (NVD)

- API 2.0: https://services.nvd.nist.gov/rest/json/cves/2.0
- Documentation: https://nvd.nist.gov/developers/vulnerabilities
- NVD API keys must be stored outside source control. Respect the current API rate limits.

## Provenance rules

For every imported dataset, record provider, exact URL, retrieval timestamp, checksum, license, feature schema/version, label source and train/test split. Keep raw archives in `datasets/cache/` (ignored) and never commit binaries.
