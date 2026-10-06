# Third-party provenance

This project keeps upstream code and adapted work distinguishable.

- `LikeACloud7/ai-trend`, revision `e20dfc1eebff33c0ce635f26be70cce82ae6bacd`, MIT License.
  Its official ACL Anthology/OpenReview collection approach informed `root_paper_lab/venues.py`.
  The dashboard, generated dataset, and keyword taxonomy were not copied. The adapted collector adds
  bounded retrieval, immutable source snapshots, explicit failure states, and a separate BK21+ baseline.
- `Silung/scholar-search-mcp`, revision `1392e7e6f483bb2fdbef42e37610b82620612ee7`, MIT License.
  An unmodified reviewed snapshot is under `vendor/scholar-search-mcp`.
- `Future-House/paper-qa`, revision `57e89f7223b0960d5ee5ea048c69e3c47e088572`, Apache-2.0.
  An unmodified reviewed snapshot is under `vendor/paper-qa`; runtime installation is version-pinned.

BK21+ classifications are research metadata from the dated public list, not software-derived quality
scores. The source and baseline date are recorded on every classification.
