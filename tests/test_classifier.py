from niyet.classifier import (
    LabeledText,
    cross_validate_tfidf,
    evaluate_tfidf_baseline,
)


def sample_rows():
    rows = []
    samples = {
        "ask": [
            "Python hatasını nasıl çözebilirim?",
            "Sensör neden veri göndermiyor?",
            "Bu bağlantı sorununu nasıl düzeltebilirim?",
            "Kod burada neden çalışmıyor?",
            "Bu hata için nereden başlamalıyım?",
            "Kart neden yeniden başlıyor?",
            "Bu sorguyu nasıl hızlandırabilirim?",
            "Servis neden açılışta başlamıyor?",
        ],
        "feedback": [
            "Bu tasarım hakkında ne düşünüyorsunuz?",
            "Sunumumda neyi değiştirmeliyim?",
            "Logoya yorum yapabilir misiniz?",
            "Bu fikir sizce anlaşılır mı?",
            "Bu sayfada ilk neyi düzeltmeliyim?",
            "Poster düzeni sizce okunuyor mu?",
            "Demo girişini fazla uzun buldunuz mu?",
            "Bu grafiği daha net nasıl gösterebilirim?",
        ],
        "collaborate": [
            "Projeye yazılımcı ekip arkadaşı arıyorum.",
            "Birlikte robot yapmak isteyen var mı?",
            "Araştırma için ortak arıyoruz.",
            "Bu etkinliği beraber düzenlemek isteyen var mı?",
            "Frontend bilen biri ekibe katılmak ister mi?",
            "Çalışma grubu kuruyoruz, katılmak isteyen var mı?",
            "Veri etiketleme için ikinci kişi arıyoruz.",
            "Drone projesine CAD bilen ekip arkadaşı arıyoruz.",
        ],
        "discuss": [
            "Sizce açık kaynak modeller daha mı iyi?",
            "Uzaktan eğitim hakkında ne düşünüyorsunuz?",
            "Bu konuda farklı görüşleri merak ediyorum.",
            "Sizce küçük ekipler mi daha verimli?",
            "Kronolojik akış sizce daha mı iyi?",
            "AI moderasyon son kararı vermeli mi?",
            "Hazır modül kullanmak öğrenmeyi azaltır mı?",
            "Sosyal ağlar watch time yerine neyi optimize etmeli?",
        ],
    }
    for label, texts in samples.items():
        for index, text in enumerate(texts):
            rows.append(LabeledText(text, label, f"{label}-{index}"))
    return rows


def test_group_split_baseline_runs_without_group_leakage():
    rows = sample_rows()
    result = evaluate_tfidf_baseline(rows, test_size=0.25, random_state=3)

    assert result.train_size + result.test_size == len(rows)
    assert 0.0 <= result.macro_f1 <= 1.0


def test_grouped_cross_validation_returns_all_folds():
    result = cross_validate_tfidf(sample_rows(), n_splits=4, random_state=7)

    assert result.folds == 4
    assert len(result.fold_macro_f1) == 4
    assert len(result.fold_accuracies) == 4
    assert 0.0 <= result.macro_f1_mean <= 1.0
    assert 0.0 <= result.accuracy_mean <= 1.0
