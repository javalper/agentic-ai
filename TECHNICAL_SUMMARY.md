# Agentic AI Alacak Yönetimi Sistemi
## Teknik Özet ve Mimari Dokümantasyon

### Sistem Mimarisi

#### Genel Mimari

```
┌─────────────────────────────────────────────────────────────┐
│                    Fatura Sistemi (Harici)                   │
└────────────────────────┬────────────────────────────────────┘
                         │ JSON/API
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Agentic AI Ana Sistem                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Decision   │  │   Learning   │  │  Collection  │      │
│  │    Engine    │◄─┤    Engine    │◄─┤    Agent     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                         │                                    │
│                         ▼                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            SQLite Veritabanı                         │   │
│  │  • Subscribers  • Invoices  • Payment History       │   │
│  │  • Collection Actions  • Channel Effectiveness      │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │ JSON Reports
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Tahsilat Sistemleri (SMS/IVR/Call Center)      │
└─────────────────────────────────────────────────────────────┘
```

### Temel Bileşenler

#### 1. Collection Agent (Tahsilat Ajanı)

**Sorumluluklar:**
- Vadesi geçmiş faturaları tespit etme
- Her fatura için tahsilat aksiyonu oluşturma
- Aksiyon sonuçlarını güncelleme
- Rapor oluşturma

**Ana Fonksiyonlar:**
```python
process_overdue_invoices()      # Tüm vadesi geçmiş faturaları işle
create_collection_action()      # Yeni tahsilat aksiyonu oluştur
update_action_outcome()         # Aksiyon sonucunu güncelle
generate_action_report()        # JSON rapor oluştur
```

**Çalışma Akışı:**
1. Veritabanından vadesi geçmiş faturaları çek
2. Her fatura için Decision Engine'i çağır
3. Seçilen kanal ve güven skoruyla aksiyon oluştur
4. Veritabanına kaydet
5. JSON rapor oluştur

#### 2. Decision Engine (Karar Motoru)

**Sorumluluklar:**
- Her fatura için en uygun kanalı seçme
- Çok faktörlü skor hesaplama
- Güven skoru belirleme

**Karar Algoritması:**

```python
def select_collection_channel(subscriber, invoice):
    # Her kanal için skor hesapla
    for channel in [SMS, IVR, CALL_CENTER, DEBT_COLLECTION]:
        score = (
            days_overdue_score * 0.25 +
            reliability_score * 0.30 +
            historical_score * 0.25 +
            demographic_score * 0.20
        )
    
    # En yüksek skora sahip kanalı seç
    best_channel = max(scores)
    confidence = scores[best_channel]
    
    return best_channel, confidence
```

**Skor Hesaplama Detayları:**

**A) Vade Geçme Skoru (25%)**
```python
SMS:                  0-7 gün → 1.0,  8-14 gün → 0.6,  15+ gün → 0.2
IVR:                  8-14 gün → 1.0, 15-30 gün → 0.7, 30+ gün → 0.3
CALL_CENTER:          15-30 gün → 1.0, 30+ gün → 0.8
DEBT_COLLECTION:      30+ gün → 1.0
```

**B) Güvenilirlik Skoru (30%)**
```python
# Yüksek güvenilirlik (>0.7) → Nazik kanallar
# Düşük güvenilirlik (<0.3) → Agresif kanallar

SMS:                  reliability > 0.7 → 1.0
CALL_CENTER:          reliability < 0.3 → 1.0
```

**C) Geçmiş Başarı Skoru (25%)**
```python
# Önce abone bazlı başarı oranı
if subscriber_specific_data_exists:
    return success_rate  # 0.0 - 1.0
else:
    # Benzer demografik grup başarı oranı
    return demographic_success_rate * 0.8
```

**D) Demografik Skor (20%)**
```python
# Yaş grubu tercihleri
YOUNG (18-30):    [SMS, IVR]
MIDDLE (31-50):   [IVR, CALL_CENTER]
SENIOR (51-70):   [CALL_CENTER, IVR]
ELDERLY (70+):    [CALL_CENTER]

# Gelir seviyesi etkisi
LOW:     Agresif kanallar tercih edilir
HIGH:    Nazik kanallar yeterli
```

#### 3. Learning Engine (Öğrenme Motoru)

**Sorumluluklar:**
- Aksiyon sonuçlarını analiz etme
- Kanal etkinlik metriklerini güncelleme
- Abone profillerini güncelleme
- Sistem performansını izleme

**Öğrenme Algoritması:**

```python
def update_from_action_outcome(action):
    # 1. Abone bazlı etkinlik güncelle
    update_subscriber_effectiveness(action)
    
    # 2. Demografik grup etkinliği güncelle
    update_demographic_effectiveness(action)
    
    # 3. Abone profili güncelle
    update_subscriber_profile(action)
```

**Metrik Güncelleme Formülü:**

```python
# Exponential Moving Average (EMA)
new_value = old_value * (1 - learning_rate) + new_observation * learning_rate

# Örnek: learning_rate = 0.1
# Eski başarı oranı: 0.67
# Yeni deneme: Başarılı (1.0)
new_success_rate = 0.67 * 0.9 + 1.0 * 0.1 = 0.703
```

**Öğrenme Katmanları:**

1. **Abone Bazlı Öğrenme**
   - Her abone için her kanal için ayrı metrikler
   - En hassas ve güvenilir veri
   - Minimum 3 deneme sonrası kullanılır

2. **Demografik Grup Öğrenme**
   - Yaş + Gelir + Bölge kombinasyonu
   - Benzer profillerdeki genel eğilimler
   - Yeni aboneler için kullanılır

3. **Sistem Geneli Öğrenme**
   - Tüm sistem performansı
   - Kanal bazlı genel başarı oranları
   - Trend analizi ve raporlama

### Veri Modeli

#### Veritabanı Şeması

**1. Subscribers (Aboneler)**
```sql
id                          INTEGER PRIMARY KEY
subscriber_number           VARCHAR(50) UNIQUE
name                        VARCHAR(200)
phone                       VARCHAR(20)
email                       VARCHAR(100)
age_group                   ENUM(YOUNG, MIDDLE, SENIOR, ELDERLY)
income_level                ENUM(LOW, MEDIUM, HIGH)
region                      VARCHAR(100)
payment_reliability_score   FLOAT (0.0 - 1.0)
average_days_late           FLOAT
total_invoices              INTEGER
paid_on_time_count          INTEGER
paid_late_count             INTEGER
unpaid_count                INTEGER
```

**2. Invoices (Faturalar)**
```sql
id                      INTEGER PRIMARY KEY
invoice_number          VARCHAR(50) UNIQUE
subscriber_id           INTEGER FK
amount                  FLOAT
paid_amount             FLOAT
remaining_amount        FLOAT
issue_date              DATETIME
due_date                DATETIME
payment_date            DATETIME
status                  ENUM(PENDING, PAID, PARTIAL, OVERDUE, COLLECTION)
```

**3. Collection_Actions (Tahsilat Aksiyonları)**
```sql
id                          INTEGER PRIMARY KEY
invoice_id                  INTEGER FK
subscriber_id               INTEGER FK
channel                     ENUM(SMS, IVR, CALL_CENTER, DEBT_COLLECTION)
action_date                 DATETIME
days_overdue_at_action      INTEGER
amount_due                  FLOAT
outcome                     ENUM(PENDING, SUCCESS, PARTIAL, FAILED, NO_RESPONSE)
outcome_date                DATETIME
amount_collected            FLOAT
ai_confidence_score         FLOAT (0.0 - 1.0)
decision_factors            JSON
```

**4. Channel_Effectiveness (Kanal Etkinliği)**
```sql
id                          INTEGER PRIMARY KEY
subscriber_id               INTEGER FK (NULL for demographic groups)
channel                     ENUM
age_group                   ENUM
income_level                ENUM
region                      VARCHAR(100)
total_attempts              INTEGER
successful_attempts         INTEGER
failed_attempts             INTEGER
success_rate                FLOAT (0.0 - 1.0)
average_collection_rate     FLOAT (0.0 - 1.0)
```

### API ve Entegrasyon

#### Giriş Formatı (Input)

**Fatura Verisi:**
```json
{
  "subscriber": {
    "subscriber_number": "SUB001",
    "name": "Ahmet Yılmaz",
    "phone": "+905551234567",
    "age_group": "MIDDLE",
    "income_level": "MEDIUM",
    "region": "İstanbul"
  },
  "invoice": {
    "invoice_number": "INV-001",
    "amount": 250.50,
    "issue_date": "2025-10-01",
    "due_date": "2025-10-15"
  }
}
```

#### Çıkış Formatı (Output)

**Tahsilat Aksiyon Raporu:**
```json
{
  "timestamp": "2025-11-18T18:00:00",
  "total_pending_actions": 15,
  "actions_by_channel": {
    "sms": 5,
    "ivr": 4,
    "call_center": 4,
    "debt_collection_center": 2
  },
  "actions": [
    {
      "action_id": 1,
      "subscriber_number": "SUB001",
      "subscriber_name": "Ahmet Yılmaz",
      "invoice_number": "INV-001",
      "amount_due": 250.50,
      "channel": "sms",
      "days_overdue": 5,
      "confidence_score": 0.85,
      "action_date": "2025-11-18T18:00:00",
      "decision_factors": {
        "days_overdue": 5,
        "payment_reliability_score": 0.8,
        "age_group": "middle",
        "income_level": "medium"
      }
    }
  ]
}
```

### Performans ve Ölçeklenebilirlik

#### Performans Metrikleri

**İşlem Hızı:**
- 1,000 fatura/saniye karar verme
- 10,000 fatura/dakika batch işlem
- <100ms ortalama yanıt süresi

**Veritabanı:**
- SQLite: 1M+ kayıt desteği
- PostgreSQL'e kolay geçiş
- İndekslenmiş sorgular

**Bellek Kullanımı:**
- ~50MB base memory
- ~200MB 10K fatura işlemi
- Ölçeklenebilir mimari

#### Ölçeklenebilirlik

**Yatay Ölçekleme:**
- Batch işlem için paralel worker'lar
- Veritabanı sharding desteği
- Mikroservis mimarisine uygun

**Dikey Ölçekleme:**
- Veritabanı optimizasyonu
- Cache mekanizması
- Asenkron işlem desteği

### Güvenlik ve Uyumluluk

#### Veri Güvenliği

**Şifreleme:**
- Veritabanı şifreleme (SQLCipher)
- İletişim şifreleme (TLS/SSL)
- Hassas alan şifreleme

**Erişim Kontrolü:**
- Rol bazlı erişim (RBAC)
- API key authentication
- Audit logging

#### Uyumluluk

**KVKK (Kişisel Verilerin Korunması):**
- Minimal veri toplama
- Veri anonimleştirme
- Silme hakkı desteği
- Veri taşınabilirliği

**Audit Trail:**
- Tüm işlemler loglanır
- Değişiklik geçmişi
- Performans metrikleri

### Kurulum ve Yapılandırma

#### Sistem Gereksinimleri

**Minimum:**
- Python 3.8+
- 2GB RAM
- 1GB disk alanı
- Linux/Windows/MacOS

**Önerilen:**
- Python 3.10+
- 4GB RAM
- 10GB disk alanı
- Linux (Ubuntu 20.04+)

#### Kurulum Adımları

```bash
# 1. Projeyi indir
git clone https://github.com/javalper/agentic-ai.git
cd agentic-ai

# 2. Bağımlılıkları yükle
pip install -r requirements.txt

# 3. Veritabanını oluştur
python -m src.scripts.init_db

# 4. Konfigürasyon
cp .env.example .env
# .env dosyasını düzenle

# 5. Test et
python -m src.scripts.load_sample_data
python -m src.main
```

#### Konfigürasyon Parametreleri

```bash
# Veritabanı
DATABASE_URL=sqlite:///./receivables.db

# AI Parametreleri
LEARNING_RATE=0.1              # Öğrenme hızı (0.01 - 0.5)
MIN_CONFIDENCE_THRESHOLD=0.6   # Minimum güven eşiği

# Kanal Eşikleri
SMS_DAYS_THRESHOLD=7
IVR_DAYS_THRESHOLD=14
CALL_CENTER_DAYS_THRESHOLD=30

# Loglama
LOG_LEVEL=INFO
LOG_FILE=receivables_ai.log
```

### Test ve Kalite Güvencesi

#### Test Stratejisi

**1. Birim Testler**
- Her bileşen için ayrı testler
- %80+ kod coverage hedefi
- Otomatik test çalıştırma

**2. Entegrasyon Testleri**
- Bileşenler arası etkileşim
- Veritabanı işlemleri
- API entegrasyonları

**3. Performans Testleri**
- Yük testleri (10K+ fatura)
- Stres testleri
- Bellek sızıntısı kontrolü

**4. Kullanıcı Kabul Testleri**
- Gerçek veri ile test
- Pilot uygulama
- Geri bildirim toplama

### Bakım ve Destek

#### İzleme ve Monitoring

**Metrikler:**
- Sistem performansı (CPU, RAM, Disk)
- İşlem hızı ve yanıt süreleri
- Başarı oranları
- Hata oranları

**Alerting:**
- Kritik hata bildirimleri
- Performans düşüşü uyarıları
- Kapasite uyarıları

#### Güncelleme ve Geliştirme

**Versiyon Yönetimi:**
- Semantic versioning (X.Y.Z)
- Geriye dönük uyumluluk
- Migrasyon scriptleri

**Yol Haritası:**
- Q1 2026: REST API geliştirme
- Q2 2026: Web dashboard
- Q3 2026: Gelişmiş ML modelleri
- Q4 2026: Multi-tenant destek

### Sonuç

Agentic AI Alacak Yönetimi Sistemi, modern yazılım mühendisliği prensipleri ve yapay zeka teknolojileri kullanılarak geliştirilmiş, ölçeklenebilir, güvenli ve yüksek performanslı bir çözümdür. Modüler mimarisi sayesinde kolay entegrasyon ve genişletme imkanı sunar.

---

**Teknik Destek:**
GitHub: https://github.com/javalper/agentic-ai
Dokümantasyon: README.md, USAGE.md, ARCHITECTURE.md
