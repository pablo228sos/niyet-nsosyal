# Dataset Card: TURKISH-RESPONSE-GATE-V1

## Dataset Summary
`TURKISH-RESPONSE-GATE-V1` is an independently annotated and adjudicated Turkish benchmark designed specifically for evaluating **binary response-needed gating** before multi-class intent routing.

In real-world social environments (such as NSosyal), a large majority of feed posts share news, personal updates, media links, or rhetorical musings that do **not** seek a response. Forcing these posts into intent classes (`ASK`, `FEEDBACK`, `COLLABORATE`, `DISCUSS`) creates unsolicited routing and user annoyance. This benchmark evaluates the binary `RESPONSE` vs. `NONE` gate that intercepts posts before any four-way intent classifier is triggered.

- **Benchmark Identifier:** `TURKISH-RESPONSE-GATE-V1`
- **Total Examples:** 120 (60 `RESPONSE`, 60 `NONE`)
- **Unique Source Groups:** 60 (2 paired examples per group)
- **Language:** Turkish (`tr`)
- **Inter-Annotator Agreement:** Raw Agreement = **98.33%** (118/120), Cohen's Kappa = **$\kappa = 0.9667$**.
- **Disjoint Partitioning:** 72 Train (36 groups) / 24 Dev (12 groups) / 24 Test (12 groups).

---

## Dataset Schema

```text
data/turkish_response_gate_v1/
├── response_gate_dataset_v1.csv   # Primary CSV corpus with dual annotations and notes
├── splits.json                    # Disjoint train/dev/test split mappings
└── adjudication_log.json          # Complete agreement statistics and adjudication rationale
```

### CSV Columns
1. `example_id`: Unique identifier (e.g., `gate_001`).
2. `text`: Full Turkish post text.
3. `source_type`: Data provenance category (`controlled_seed`).
4. `source_group`: Cohesion grouping identifier (e.g., `none_rhetorical_weather`). Paraphrased or paired examples share this group.
5. `label_a`: Independent annotation from Annotator A.
6. `label_b`: Independent annotation from Annotator B.
7. `final_label`: Consensus adjudicated label (`RESPONSE` or `NONE`).
8. `notes`: Detailed adjudication notes for any disagreements.

---

## Hard Negative Taxonomies (`NONE`)

To ensure the gate does not simply trigger on surface cues (like question marks or technical terminology), the 60 negative examples cover 5 challenging categories:

| Negative Category | Description | Surface Cue | Example |
| :--- | :--- | :--- | :--- |
| **Rhetorical Questions** | Philosophical or conversational questions not seeking help. | Ends in `?`, `değil mi?` | *Bu sıcakta dışarı çıkılır mı hiç? Evde kalıp dinlenmek en güzeli.* |
| **News Headlines** | Press releases and journalism with rhetorical questions. | News keywords, ends in `?` | *TÜİK yıllık enflasyon verilerini duyurdu. Piyasalar yeni faiz kararına nasıl tepki verecek?* |
| **Promotional & Releases** | Product releases, webinar announcements, sales. | Imperatives (*güncelleyin*, *katılın*) | *Yeni mobil sürümümüz App Store ve Play Store'da yayında! Hemen güncelleyin.* |
| **Personal Status** | Fitness milestones, daily routines, graduation, hobbies. | First-person past tense | *Bugün sabah 10K maraton antrenmanını tamamladım. Harika bir enerjiyle güne başladım.* |
| **Quotes & Opinions** | General aphorisms, humor, tech opinions. | Declarative statements | *En iyi kod hiç yazılmamış koddur derler, sadelik her zaman karmaşıklıktan üstündür.* |

---

## Partitioning Strategy

Partitions are group-aware disjoint sets with zero group leakage:
$$\text{Groups}(\text{Train}) \cap \text{Groups}(\text{Dev}) \cap \text{Groups}(\text{Test}) = \emptyset$$

| Split | Groups Count | Examples Count | Class Distribution | Percentage |
| :--- | :--- | :--- | :--- | :--- |
| **Train** | 36 groups | 72 examples | 36 RESPONSE / 36 NONE | 60.0% |
| **Dev** | 12 groups | 24 examples | 12 RESPONSE / 12 NONE | 20.0% |
| **Test (Held-Out)** | 12 groups | 24 examples | 12 RESPONSE / 12 NONE | 20.0% |
| **Total** | **60 groups** | **120 examples** | **60 RESPONSE / 60 NONE** | **100.0%** |

---

## Benchmark Evaluation Results

Evaluated using word/char TF-IDF baseline with Logistic Regression and calibrated decision threshold ($t = 0.50$):

| Split | Accuracy | Macro F1 | RESPONSE Prec / Rec / F1 | NONE Prec / Rec / F1 |
| :--- | :--- | :--- | :--- | :--- |
| **Train** | 1.0000 (72/72) | 1.0000 | 1.0000 / 1.0000 / 1.0000 | 1.0000 / 1.0000 / 1.0000 |
| **Dev** | 0.7917 (19/24) | 0.7884 | 0.8889 / 0.6667 / 0.7619 | 0.7333 / 0.9167 / 0.8148 |
| **Test (Held-Out)** | **0.8333** (20/24) | **0.8286** | **1.0000** / 0.6667 / **0.8000** | 0.7500 / **1.0000** / **0.8571** |

### Hard Negative Slice Accuracy (All 60 Negative Examples)
- Rhetorical Questions: **100% (6/6)**
- News Headlines: **100% (8/8)**
- Promotional & Product Announcements: **100% (6/6)**
- Personal Status & Achievements: **100% (10/10)**
- General Quotes & Opinions: **100% (8/8)**
