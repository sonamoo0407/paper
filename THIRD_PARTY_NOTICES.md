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
- `marcpinet/citracer`, local reviewed revision `733adab034bdc0e64be63f188654704d8a21ae27`, MIT License, copyright Marc Pinet.
  Its analytics and HTML visualizer are reused by the citation renderers. The copyright and license are
  preserved in `licenses/citracer-MIT.txt`. The final Ubuntu HTML was generated with the VM's installed
  citracer version; its complete runtime source/version manifest still needs to be retrieved from that VM.
  Generated HTML also embeds upstream visualization dependencies, including PyVis and vis-network.
  Upstream embedded notices remain part of the archived HTML.

The KGU logo in `presentations/citation-report-20261118/assets` comes from Kyonggi University's official
UI page, https://www.kyonggi.ac.kr/www/contents.do?key=5093. Logo and university branding rights remain
with their respective owners. The presentation preserves the official artwork's colors and proportions.
The project's MIT license does not grant rights to university branding or to cited paper excerpts.

BK21+ classifications are research metadata from the dated public list, not software-derived quality
scores. The source and baseline date are recorded on every classification.
