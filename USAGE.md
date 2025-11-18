# Kullanım Kılavuzu

## Hızlı Başlangıç

### 1. Kurulum

```bash
# Bağımlılıkları yükle
pip install -r requirements.txt

# .env dosyasını oluştur
cp .env.example .env
```

### 2. Veritabanını Oluştur

```bash
python -m src.scripts.init_db
```

### 3. Örnek Veri Yükle (Opsiyonel)

```bash
python -m src.scripts.load_sample_data
```

### 4. Sistemi Çalıştır

```bash
# Tüm vadesi geçmiş faturaları işle
python -m src.main

# Belirli bir çıktı dosyasına kaydet
python -m src.main --output my_actions.json
```

## Detaylı Kullanım

### Tahsilat Aksiyonları Oluşturma

Sistem otomatik olarak vadesi geçmiş tüm faturaları tarar ve her biri için en uygun tahsilat kanalını seçer:

```bash
python -m src.main
```

Bu komut:
1. Veritabanındaki tüm vadesi geçmiş faturaları bulur
2. Her fatura için abone profilini analiz eder
3. AI agent en uygun tahsilat kanalını seçer
4. Aksiyonları veritabanına kaydeder
5. JSON formatında rapor oluşturur

### Sistem Performans Analizi

```bash
python -m src.main --analyze
```

Bu komut sistem performansını analiz eder ve şunları gösterir:
- Toplam aksiyon sayısı
- Başarılı aksiyon sayısı
- Genel başarı oranı
- Kanal bazlı performans metrikleri

### Aksiyon Sonuçlarını Simüle Etme

Test amaçlı aksiyon sonuçlarını simüle etmek için:

```bash
python -m src.scripts.simulate_outcomes
```

Bu komut:
1. Bekleyen tüm aksiyonları bulur
2. Rastgele sonuçlar atar (başarılı, kısmi başarılı, başarısız)
3. Öğrenme mekanizmasını günceller
4. Abone profillerini günceller

## Karar Verme Mantığı

### Kanal Seçimi Faktörleri

Sistem şu faktörleri değerlendirir:

1. **Vade Geçme Süresi** (Ağırlık: %25)
   - 0-7 gün: SMS tercih edilir
   - 8-14 gün: IVR tercih edilir
   - 15-30 gün: Call Center tercih edilir
   - 30+ gün: Borç Ödeme Merkezi tercih edilir

2. **Ödeme Güvenilirliği** (Ağırlık: %30)
   - Yüksek güvenilirlik (>0.7): Daha az agresif kanallar
   - Orta güvenilirlik (0.3-0.7): Dengeli yaklaşım
   - Düşük güvenilirlik (<0.3): Daha agresif kanallar

3. **Geçmiş Başarı Oranları** (Ağırlık: %25)
   - Abone bazında kanal başarı oranları
   - Benzer demografik profillerdeki başarı oranları

4. **Demografik Özellikler** (Ağırlık: %20)
   - Yaş grubu tercihleri
   - Gelir seviyesi
   - Bölgesel faktörler

### Güven Skoru

Her karar için bir güven skoru hesaplanır (0-1 arası). Eğer güven skoru minimum eşik değerinin (%60) altındaysa, sistem vade geçme süresine göre varsayılan bir kanal seçer.

## Öğrenme Mekanizması

Sistem her tahsilat girişiminin sonucunu kaydeder ve şunları günceller:

### 1. Abone Bazlı Etkinlik

Her abone için her kanal için:
- Toplam deneme sayısı
- Başarılı deneme sayısı
- Başarı oranı
- Ortalama tahsilat oranı

### 2. Demografik Etkinlik

Benzer profillerdeki aboneler için:
- Yaş grubu bazında kanal etkinliği
- Gelir seviyesi bazında kanal etkinliği
- Bölge bazında kanal etkinliği

### 3. Abone Profil Güncellemesi

Her sonuç sonrası:
- Ödeme güvenilirlik skoru güncellenir
- Ortalama gecikme süresi güncellenir
- Ödeme alışkanlık sayaçları güncellenir

## Çıktı Formatı

### JSON Rapor Yapısı

```json
{
  "timestamp": "2025-11-18T10:30:00",
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
      "action_date": "2025-11-18T10:30:00"
    }
  ]
}
```

## Veritabanı Yönetimi

### Veritabanını Sıfırlama

```python
from src.database.db_manager import DatabaseManager

db_manager = DatabaseManager()
db_manager.drop_tables()
db_manager.create_tables()
```

### Manuel Veri Ekleme

```python
from src.database.db_manager import DatabaseManager
from src.models.subscriber import Subscriber, AgeGroup, IncomeLevel

db_manager = DatabaseManager()

with db_manager.get_session() as session:
    subscriber = Subscriber(
        subscriber_number='SUB999',
        name='Yeni Abone',
        phone='+905551234567',
        age_group=AgeGroup.MIDDLE,
        income_level=IncomeLevel.MEDIUM,
        region='İstanbul'
    )
    session.add(subscriber)
```

## Konfigürasyon

`.env` dosyasında şu parametreleri ayarlayabilirsiniz:

- `DATABASE_URL`: Veritabanı bağlantı URL'si
- `LEARNING_RATE`: Öğrenme hızı (0-1 arası, varsayılan: 0.1)
- `MIN_CONFIDENCE_THRESHOLD`: Minimum güven eşiği (0-1 arası, varsayılan: 0.6)
- `SMS_DAYS_THRESHOLD`: SMS için maksimum gün eşiği (varsayılan: 7)
- `IVR_DAYS_THRESHOLD`: IVR için maksimum gün eşiği (varsayılan: 14)
- `CALL_CENTER_DAYS_THRESHOLD`: Call Center için maksimum gün eşiği (varsayılan: 30)

## Sorun Giderme

### Veritabanı Hatası

Eğer veritabanı hatası alıyorsanız:

```bash
# Veritabanını yeniden oluştur
python -m src.scripts.init_db
```

### Import Hatası

Eğer import hatası alıyorsanız, projeyi Python modülü olarak çalıştırdığınızdan emin olun:

```bash
# Doğru
python -m src.main

# Yanlış
python src/main.py
```

### Bağımlılık Hatası

```bash
# Bağımlılıkları yeniden yükle
pip install -r requirements.txt --upgrade
```
