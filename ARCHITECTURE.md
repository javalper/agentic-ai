# Sistem Mimarisi

## Genel Bakış

Bu sistem, enerji şirketleri için geliştirilmiş akıllı alacak yönetimi ve tahsilat takip sistemidir. Agentic AI prensiplerine göre tasarlanmış olup, kendi kendine öğrenen ve optimize olan bir yapıya sahiptir.

## Mimari Bileşenler

```
agentic-ai/
├── src/
│   ├── models/              # Veri modelleri
│   │   ├── subscriber.py    # Abone modeli
│   │   ├── invoice.py       # Fatura modeli
│   │   ├── payment_history.py
│   │   ├── collection_action.py
│   │   └── channel_effectiveness.py
│   ├── agent/               # AI Agent bileşenleri
│   │   ├── collection_agent.py    # Ana agent
│   │   ├── decision_engine.py     # Karar verme motoru
│   │   └── learning_engine.py     # Öğrenme motoru
│   ├── database/            # Veritabanı yönetimi
│   │   └── db_manager.py
│   ├── config/              # Konfigürasyon
│   │   └── settings.py
│   ├── scripts/             # Yardımcı scriptler
│   │   ├── init_db.py
│   │   ├── load_sample_data.py
│   │   └── simulate_outcomes.py
│   └── main.py              # Ana uygulama
├── requirements.txt
├── README.md
├── USAGE.md
└── ARCHITECTURE.md
```

## Veri Modelleri

### Subscriber (Abone)

Abone bilgilerini ve demografik özelliklerini saklar:

- Temel bilgiler: ad, telefon, email
- Demografik özellikler: yaş grubu, gelir seviyesi, bölge
- Ödeme profili: güvenilirlik skoru, ortalama gecikme, ödeme istatistikleri

**Önemli Metodlar:**
- `update_payment_score()`: Ödeme güvenilirlik skorunu günceller

### Invoice (Fatura)

Fatura bilgilerini ve durumunu saklar:

- Fatura detayları: tutar, vade tarihi, ödeme durumu
- İlişkiler: abone_id ile bağlantılı
- Durum: pending, paid, partial, overdue, collection, written_off

**Önemli Metodlar:**
- `days_overdue()`: Vade geçme gün sayısını hesaplar
- `update_status()`: Fatura durumunu günceller

### PaymentHistory (Ödeme Geçmişi)

Yapılan ödemeleri kaydeder:

- Ödeme detayları: tutar, tarih, yöntem
- Gecikme bilgisi: vade sonrası kaç gün geçtiği

### CollectionAction (Tahsilat Aksiyonu)

AI agent tarafından alınan tahsilat aksiyonlarını saklar:

- Kanal seçimi: SMS, IVR, Call Center, Debt Collection Center
- Karar faktörleri: AI güven skoru, karar nedenleri
- Sonuç: başarılı, kısmi başarılı, başarısız, yanıt yok

**Önemli Metodlar:**
- `is_successful()`: Aksiyonun başarılı olup olmadığını kontrol eder

### ChannelEffectiveness (Kanal Etkinliği)

Her kanal için etkinlik metriklerini saklar:

- Abone bazlı: belirli bir abone için kanal başarı oranları
- Demografik bazlı: benzer profillerdeki genel başarı oranları
- Metrikler: toplam deneme, başarılı deneme, başarı oranı

**Önemli Metodlar:**
- `update_metrics()`: Başarı oranını yeniden hesaplar

## AI Agent Bileşenleri

### CollectionAgent (Ana Agent)

Tahsilat sürecini yöneten ana bileşen:

**Sorumluluklar:**
1. Vadesi geçmiş faturaları tespit etme
2. Her fatura için tahsilat aksiyonu oluşturma
3. Aksiyon sonuçlarını güncelleme
4. Rapor oluşturma

**Ana Metodlar:**
- `process_overdue_invoices()`: Tüm vadesi geçmiş faturaları işler
- `create_collection_action()`: Yeni tahsilat aksiyonu oluşturur
- `update_action_outcome()`: Aksiyon sonucunu günceller ve öğrenme mekanizmasını tetikler
- `generate_action_report()`: JSON formatında rapor oluşturur

### DecisionEngine (Karar Verme Motoru)

En uygun tahsilat kanalını seçen AI motoru:

**Karar Verme Süreci:**

1. **Kanal Skorları Hesaplama**: Her kanal için 0-1 arası skor hesaplar
2. **Faktör Ağırlıklandırma**: Farklı faktörleri ağırlıklarıyla birleştirir
3. **En İyi Kanal Seçimi**: En yüksek skora sahip kanalı seçer
4. **Güven Skoru**: Kararın güvenilirliğini belirtir

**Değerlendirilen Faktörler:**

```python
CHANNEL_WEIGHTS = {
    'payment_reliability': 0.3,    # Ödeme güvenilirliği
    'days_overdue': 0.25,          # Vade geçme süresi
    'historical_success': 0.25,    # Geçmiş başarı oranları
    'demographic': 0.2             # Demografik özellikler
}
```

**Ana Metodlar:**
- `select_collection_channel()`: En uygun kanalı seçer
- `_calculate_channel_score()`: Bir kanal için toplam skoru hesaplar
- `_calculate_days_overdue_score()`: Vade geçme süresine göre skor
- `_calculate_reliability_score()`: Ödeme güvenilirliğine göre skor
- `_calculate_historical_success_score()`: Geçmiş başarılara göre skor
- `_calculate_demographic_score()`: Demografik özelliklere göre skor

### LearningEngine (Öğrenme Motoru)

Sistem performansını sürekli iyileştiren öğrenme mekanizması:

**Öğrenme Süreci:**

1. **Aksiyon Sonucu Analizi**: Her aksiyon sonrası sonuç analiz edilir
2. **Etkinlik Güncelleme**: Kanal etkinlik metrikleri güncellenir
3. **Profil Güncelleme**: Abone ödeme profili güncellenir
4. **Strateji Optimizasyonu**: Gelecek kararlar için strateji optimize edilir

**Öğrenme Katmanları:**

1. **Abone Bazlı Öğrenme**: Her abone için özel kanal tercihleri
2. **Demografik Öğrenme**: Benzer profillerdeki genel eğilimler
3. **Sistem Geneli Öğrenme**: Tüm sistem performansı

**Ana Metodlar:**
- `update_from_action_outcome()`: Aksiyon sonucundan öğrenir
- `_update_subscriber_specific_effectiveness()`: Abone bazlı metrikleri günceller
- `_update_demographic_effectiveness()`: Demografik metrikleri günceller
- `_update_subscriber_payment_profile()`: Abone profilini günceller
- `get_channel_recommendations()`: Bir abone için kanal önerileri
- `analyze_system_performance()`: Sistem geneli performans analizi

## Veri Akışı

### 1. Tahsilat Aksiyonu Oluşturma

```
Vadesi Geçmiş Fatura
    ↓
CollectionAgent.process_overdue_invoices()
    ↓
DecisionEngine.select_collection_channel()
    ↓
    ├─ Vade geçme süresi analizi
    ├─ Ödeme güvenilirliği analizi
    ├─ Geçmiş başarı oranları analizi
    └─ Demografik özellikler analizi
    ↓
Kanal Seçimi + Güven Skoru
    ↓
CollectionAction Oluşturma
    ↓
Veritabanına Kayıt
    ↓
JSON Rapor
```

### 2. Öğrenme Döngüsü

```
Aksiyon Sonucu
    ↓
CollectionAgent.update_action_outcome()
    ↓
LearningEngine.update_from_action_outcome()
    ↓
    ├─ Abone bazlı etkinlik güncelleme
    ├─ Demografik etkinlik güncelleme
    └─ Abone profil güncelleme
    ↓
Güncellenmiş Metrikler
    ↓
Gelecek Kararlar için Kullanım
```

## Veritabanı Şeması

### İlişkiler

```
Subscriber (1) ──── (N) Invoice
    │                    │
    │                    │
    └──── (N) CollectionAction (N) ────┘
    │
    └──── (N) ChannelEffectiveness
    
Invoice (1) ──── (N) PaymentHistory
```

### İndeksler

Performans için önemli indeksler:

- `subscribers.subscriber_number` (UNIQUE)
- `invoices.invoice_number` (UNIQUE)
- `invoices.subscriber_id`
- `collection_actions.invoice_id`
- `collection_actions.subscriber_id`
- `payment_history.invoice_id`
- `payment_history.subscriber_id`
- `channel_effectiveness.subscriber_id`

## Konfigürasyon Sistemi

### Ayarlanabilir Parametreler

1. **Öğrenme Parametreleri**
   - `LEARNING_RATE`: Yeni bilgilerin eski bilgilere göre ağırlığı
   - `MIN_CONFIDENCE_THRESHOLD`: Minimum güven eşiği

2. **Kanal Eşikleri**
   - `SMS_DAYS_THRESHOLD`: SMS için maksimum gün
   - `IVR_DAYS_THRESHOLD`: IVR için maksimum gün
   - `CALL_CENTER_DAYS_THRESHOLD`: Call Center için maksimum gün

3. **Ağırlıklar**
   - `CHANNEL_WEIGHTS`: Karar faktörlerinin ağırlıkları

4. **Demografik Tercihler**
   - `DEMOGRAPHIC_PREFERENCES`: Yaş gruplarına göre kanal tercihleri
   - `INCOME_LEVEL_THRESHOLDS`: Gelir seviyelerine göre eşikler

## Genişletilebilirlik

### Yeni Kanal Ekleme

1. `CollectionChannel` enum'una yeni kanal ekle
2. `DecisionEngine._calculate_days_overdue_score()` metodunu güncelle
3. `DecisionEngine._calculate_reliability_score()` metodunu güncelle
4. Konfigürasyona yeni kanal parametreleri ekle

### Yeni Karar Faktörü Ekleme

1. `DecisionEngine._calculate_channel_score()` metoduna yeni faktör ekle
2. Yeni faktör için hesaplama metodu oluştur
3. `CHANNEL_WEIGHTS` konfigürasyonuna yeni ağırlık ekle
4. `decision_factors` dictionary'sine yeni faktör bilgisi ekle

### Yeni Öğrenme Metrikleri

1. `ChannelEffectiveness` modeline yeni alan ekle
2. `LearningEngine` metodlarını güncelle
3. Yeni metriği raporlara ekle

## Performans Optimizasyonu

### Veritabanı Sorguları

- Eager loading kullanımı
- İndeks optimizasyonu
- Batch işlemler

### Bellek Yönetimi

- Session yönetimi (context manager)
- Lazy loading
- Pagination (büyük veri setleri için)

### Ölçeklenebilirlik

- Modüler mimari
- Bağımsız bileşenler
- Kolay test edilebilirlik

## Güvenlik

### Veri Güvenliği

- Hassas bilgilerin şifrelenmesi (gelecek sürüm)
- SQL injection koruması (SQLAlchemy ORM)
- Environment variables ile konfigürasyon

### Erişim Kontrolü

- Veritabanı erişim kontrolü
- API authentication (gelecek sürüm)
- Audit logging (gelecek sürüm)
