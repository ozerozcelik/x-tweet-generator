# X Algorithm Tweet Generator

X (Twitter) algoritmasının For You feed puanlama sistemine dayanan tweet optimizasyon ve oluşturma aracı.

## Algoritma Hakkında

Bu tool, [X Algorithm](https://github.com/xai-org/x-algorithm) reposundaki bilgilere dayanır. X'in For You algoritması şu faktörleri değerlendirir:

### Pozitif Sinyaller (Engagement Artırır)
| Eylem | Ağırlık | Açıklama |
|-------|---------|----------|
| Follow | +3.0 | Kullanıcının sizi takip etmesi |
| Quote | +2.5 | Alıntı tweet |
| Repost | +2.0 | Retweet |
| Share | +1.8 | Paylaşım |
| Reply | +1.5 | Yanıt |
| Favorite | +1.0 | Beğeni |

### Negatif Sinyaller (Engagement Düşürür)
| Eylem | Ağırlık | Açıklama |
|-------|---------|----------|
| Report | -10.0 | Şikayet |
| Block | -5.0 | Engelleme |
| Mute | -3.0 | Sessize alma |
| Not Interested | -2.0 | İlgilenmiyorum |

## Kurulum

```bash
git clone https://github.com/YOUR_USERNAME/x-tweet-generator.git
cd x-tweet-generator
pip install -r requirements.txt
```

## Kullanım

### 1. Tweet Analizi

Tweet'inizi algoritma perspektifinden analiz edin:

```bash
python tweet_generator.py analyze "Tweet'inizi buraya yazın"
```

**Örnek:**
```bash
python tweet_generator.py analyze "Yapay zeka hakkında düşüncelerim var ama paylaşmaktan çekiniyorum"
```

**Çıktı:**
```
📊 TWEET ANALİZİ
==================================================

🎯 Algoritma Skoru: 72.0/100

❌ Zayıf Yönler:
   • Soru içermiyor - reply olasılığı düşük

💡 Öneriler:
   • 1-3 emoji eklemek görünürlüğü artırabilir
   • Satır araları eklemek okunabilirliği artırır
   • Bir call to action ekleyin (örn: 'Ne düşünüyorsunuz?')
```

### 2. Şablon Listesi

Yüksek engagement şablonlarını görüntüleyin:

```bash
python tweet_generator.py templates
```

### 3. Şablondan Tweet Oluşturma

```bash
python tweet_generator.py generate thread_hook --vars '{"konu": "Yapay Zeka", "sayi": "5"}'
```

**Çıktı:**
```
🐦 OLUŞTURULAN TWEET
==================================================

🧵 Yapay Zeka hakkında bilmeniz gereken 5 şey:

(Thread)

📏 Karakter: 58/280
```

### 4. Tweet Optimizasyonu

Mevcut tweet'inizi optimize edin:

```bash
python tweet_generator.py optimize "Bu harika bir ürün https://external-link.com #tag1 #tag2 #tag3 #tag4 #tag5"
```

### 5. Konu Önerileri

Belirli bir konu için tweet fikirleri alın:

```bash
python tweet_generator.py suggest "startup" --style professional
python tweet_generator.py suggest "teknoloji" --style casual
python tweet_generator.py suggest "iş hayatı" --style provocative
```

### 6. Paylaşım Zamanları

En iyi paylaşım zamanlarını öğrenin:

```bash
python tweet_generator.py times
```

## Şablonlar

| Şablon | Engagement Boost | Açıklama |
|--------|------------------|----------|
| `thread_hook` | +35% | Thread başlangıcı |
| `hot_take` | +40% | Tartışmalı görüş |
| `story_hook` | +25% | Hikaye formatı |
| `question_poll` | +30% | Anket tarzı |
| `value_list` | +20% | Değer listesi |
| `before_after` | +25% | Dönüşüm hikayesi |
| `myth_buster` | +30% | Mit kırıcı |
| `prediction` | +20% | Tahmin tweeti |
| `controversial_opinion` | +35% | Cesur görüş |
| `simple_insight` | +15% | Basit içgörü |

## Algoritma İpuçları

### Engagement Artıran Faktörler
- Soru sormak (reply'ı artırır)
- Thread formatı kullanmak
- Satır araları ile okunabilirlik
- 1-3 emoji kullanımı
- Call to action eklemek
- Kişisel deneyim paylaşmak

### Engagement Düşüren Faktörler
- Dış linkler (X dışına çıkış)
- 3'ten fazla hashtag
- Tamamı büyük harf
- Spam kelimeleri
- Çok fazla emoji (>5)

### En İyi Paylaşım Zamanları
- **Hafta içi:** 08:00-09:00, 12:00-13:00, 17:00-18:00, 21:00-22:00
- **Hafta sonu:** 10:00-11:00, 14:00-15:00, 20:00-21:00
- **En iyi günler:** Salı, Çarşamba, Perşembe

## Python API Kullanımı

```python
from tweet_generator import XAlgorithmTweetGenerator

generator = XAlgorithmTweetGenerator()

# Tweet analizi
analysis = generator.analyze_tweet("Tweet metniniz")
print(f"Skor: {analysis.score}")
print(f"Güçlü yönler: {analysis.strengths}")
print(f"Öneriler: {analysis.suggestions}")

# Şablondan tweet oluşturma
tweet = generator.generate_from_template("thread_hook", {
    "konu": "Python",
    "sayi": "7"
})

# Tweet optimizasyonu
optimized = generator.optimize_tweet("Orijinal tweet")

# Konu önerileri
suggestions = generator.suggest_improvements("AI", style="professional")
```

## Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit edin (`git commit -m 'Add amazing feature'`)
4. Push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

## Lisans

MIT License - Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## Referanslar

- [X Algorithm Repository](https://github.com/xai-org/x-algorithm)
- X'in resmi algoritma açıklamaları

---

**Not:** Bu tool, X'in açık kaynak algoritma bilgilerine dayanır. Gerçek algoritma ağırlıkları gizlidir ve buradaki değerler tahminîdir.
