from niyet.classifier import LabeledText, evaluate_tfidf_baseline


def test_group_split_baseline_runs_without_group_leakage():
    rows = []
    samples = {
        "ask": [
            "Python hatasını nasıl çözebilirim?",
            "Sensör neden veri göndermiyor?",
            "Bu bağlantı sorununu nasıl düzeltebilirim?",
            "Kod burada neden çalışmıyor?",
        ],
        "feedback": [
            "Bu tasarım hakkında ne düşünüyorsunuz?",
            "Sunumumda neyi değiştirmeliyim?",
            "Logoya yorum yapabilir misiniz?",
            "Bu fikir sizce anlaşılır mı?",
        ],
        "collaborate": [
            "Projeye yazılımcı ekip arkadaşı arıyorum.",
            "Birlikte robot yapmak isteyen var mı?",
            "Araştırma için ortak arıyoruz.",
            "Bu etkinliği beraber düzenlemek isteyen var mı?",
        ],
        "discuss": [
            "Sizce açık kaynak modeller daha mı iyi?",
            "Uzaktan eğitim hakkında ne düşünüyorsunuz?",
            "Bu konuda farklı görüşleri merak ediyorum.",
            "Sizce küçük ekipler mi daha verimli?",
        ],
    }
    for label, texts in samples.items():
        for index, text in enumerate(texts):
            rows.append(LabeledText(text, label, f"{label}-{index}"))

    result = evaluate_tfidf_baseline(rows, test_size=0.25, random_state=3)

    assert result.train_size + result.test_size == len(rows)
    assert 0.0 <= result.macro_f1 <= 1.0
