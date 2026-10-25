# Dataset Card: TURKISH-INTENT-V1

## Dataset Summary
`TURKISH-INTENT-V1` is an independently annotated and adjudicated Turkish intent classification benchmark containing **120 authentic Turkish social posts** balanced evenly across the four core NIYET intent categories: `ASK`, `FEEDBACK`, `COLLABORATE`, and `DISCUSS` (30 examples per class).

The dataset is partitioned into strictly disjoint source groups to prevent data leakage between paraphrases and topical variations.

- **Benchmark Identifier:** `TURKISH-INTENT-V1`
- **Total Examples:** 120
- **Unique Source Groups:** 60 (2 paired examples per group)
- **Language:** Turkish (`tr`)
- **Annotation Strategy:** Dual independent annotators (`label_a`, `label_b`) with formal adjudication and disagreement logging.
- **Inter-Annotator Agreement:** Raw Agreement = **95.83%** (115/120), Cohen's Kappa = **$\kappa = 0.9444$**.

---

## Intent Taxonomy

| Class | Definition | Typical User Goal | Example |
| :--- | :--- | :--- | :--- |
| `ASK` | Direct request for an answer, troubleshooting, or technical solution to a specific concrete problem. | Problem solving / debugging | *ESP32 kartım Wi-Fi bağlantısını birkaç dakikada bir kaybediyor. Nereden kontrol etmeye başlamalıyım?* |
| `FEEDBACK` | Seeking critique, evaluation, or suggestions on an author-created artifact (design, pitch, text, code architecture). | Review / improvement | *Yeni projemiz için bu landing page'i hazırladım. İlk bakışta en zayıf tarafı sizce ne?* |
| `COLLABORATE` | Recruiting partners or contributors to build, research, co-found, or hack on a shared project. | Teaming / co-creation | *Robotik yarışması için görüntü işleme ve ROS bilen bir ekip arkadaşı arıyoruz.* |
| `DISCUSS` | Open-ended architectural, philosophical, or ecosystem debate without a single factual answer. | Exchange of views | *Sizce küçük ekiplerde açık kaynak model kullanmak uzun vadede daha mantıklı mı?* |

---

## Dataset Structure & Files

```text
data/turkish_intent_v1/
├── intent_dataset_v1.csv   # Primary CSV corpus with dual annotations and adjudication
├── splits.json             # Group-aware disjoint train/dev/test split mappings
└── adjudication_log.json   # Full agreement metrics and adjudication rationale log
```

### CSV Schema (`intent_dataset_v1.csv`)
1. `example_id`: Unique identifier (e.g., `intent_001`).
2. `text`: Authentic Turkish post text.
3. `source_type`: Data provenance category (`controlled_seed`, `team_written`, `public`).
4. `source_group`: Cohesion grouping identifier (e.g., `ask_wifi`). Paraphrased or paired examples share this identifier.
5. `label_a`: Independent annotation from Annotator A.
6. `label_b`: Independent annotation from Annotator B.
7. `final_label`: Consensus adjudicated label.
8. `notes`: Detailed adjudication notes for any disagreements between annotators.

---

## Split Partitioning

Partitions are generated using **group-aware disjoint sampling** ensuring that:
$$\text{Groups}(\text{Train}) \cap \text{Groups}(\text{Dev}) \cap \text{Groups}(\text{Test}) = \emptyset$$

| Split | Groups Count | Examples Count | Class Distribution | Percentage |
| :--- | :--- | :--- | :--- | :--- |
| **Train** | 36 groups | 72 examples | 18 per class (balanced) | 60.0% |
| **Dev** | 12 groups | 24 examples | 6 per class (balanced) | 20.0% |
| **Test** | 12 groups | 24 examples | 6 per class (balanced) | 20.0% |
| **Total** | **60 groups** | **120 examples** | **30 per class (balanced)** | **100.0%** |

---

## Adjudication & Disagreement Analysis
All 5 annotator disagreements (4.17% of total corpus) were reviewed and documented in `adjudication_log.json`:
- **`ask_math` (`intent_007`):** Author asked *"Bu olasılık sorusunda neden kombinasyon kullanıyoruz, mantığını biri açıklayabilir mi?"*. Disagreement between `ASK` and `DISCUSS`. Adjudicated as `ASK` because it concerns a concrete mathematical question with a verifiable solution rather than an open opinion exchange.
- **`fb_api_design` (`intent_039`):** Author requested review of REST endpoint naming against standards. Disagreement between `FEEDBACK` and `ASK`. Adjudicated as `FEEDBACK` because the user designed an architectural artifact and requested evaluation.
- **`fb_license` (`intent_043`):** Author evaluated licensing trade-offs for their library. Disagreement between `FEEDBACK` and `DISCUSS`. Adjudicated as `FEEDBACK` as it solicits feedback on an author's specific pending project decision.
- **`collab_a11y` (`intent_081`):** Working group invitation phrased as *"Katılmak ister misiniz?"*. Disagreement between `COLLABORATE` and `DISCUSS`. Adjudicated as `COLLABORATE` because the intent is working group recruitment.
- **`disc_graphql_rest` (`intent_109`):** Architecture trade-off discussion. Disagreement between `DISCUSS` and `ASK`. Adjudicated as `DISCUSS` as it is an open-ended debate without a single truth value.

---

## Benchmark Baseline Results
Evaluated using the committed word/char TF-IDF feature union with Logistic Regression:

| Split | Accuracy | Macro F1 | Weighted F1 |
| :--- | :--- | :--- | :--- |
| **Train** | 1.0000 (72/72) | 1.0000 | 1.0000 |
| **Dev** | 0.7917 (19/24) | 0.7645 | 0.7812 |
| **Test (Held-Out)** | **0.9167** (22/24) | **0.9188** | **0.9167** |

### Test Split Per-Class Performance
- `ASK`: Precision 1.0000, Recall 0.8333, **F1 = 0.9091**
- `FEEDBACK`: Precision 1.0000, Recall 0.8333, **F1 = 0.9091**
- `COLLABORATE`: Precision 1.0000, Recall 1.0000, **F1 = 1.0000**
- `DISCUSS`: Precision 0.7500, Recall 1.0000, **F1 = 0.8571**
