# Agentic AI - Alacak Yönetimi ve Yasal Takip Sistemi

Bu proje, enerji şirketleri için geliştirilmiş akıllı alacak yönetimi ve tahsilat takip sistemidir. Sistem, abone davranışlarını analiz ederek en uygun tahsilat kanalını otomatik olarak seçer ve öğrenerek kendini geliştirir.

## Özellikler

- **Akıllı Kanal Seçimi**: Abonenin geçmiş ödeme alışkanlıkları ve demografik özelliklerine göre en uygun tahsilat kanalını seçer
- **Çoklu Tahsilat Kanalları**:
  - SMS bildirimi
  - IVR (Otomatik sesli arama)
  - Call Center araması
  - Ulusal Borç Ödeme Merkezi bildirimi
- **Öğrenen Sistem**: Her tahsilat girişiminin sonucunu kaydeder ve başarı oranlarını artırmak için stratejisini geliştirir
- **Otomatik Karar Verme**: Fatura vade tarihi ve abone profili bazında otomatik aksiyon alır
- **Veritabanı Entegrasyonu**: SQLite veritabanı ile tüm verileri saklar ve takip eder

## Sistem Mimarisi

Sistem şu bileşenlerden oluşur:

1. **Veri Modelleri** (`models/`): Abone, fatura, ödeme geçmişi ve tahsilat aksiyonları
2. **AI Agent** (`agent/`): Karar verme ve öğrenme mekanizması
3. **Veritabanı** (`database/`): SQLite ile veri yönetimi
4. **Konfigürasyon** (`config/`): Sistem ayarları ve parametreler

## Kurulum

```bash
# Bağımlılıkları yükle
pip install -r requirements.txt

# Veritabanını oluştur
python -m src.database.init_db

# Örnek veri yükle (opsiyonel)
python -m src.scripts.load_sample_data
```

## Kullanım

```bash
# Sistemi çalıştır
python -m src.main

# Belirli bir ay için işle
python -m src.main --month 2025-11

# Test modu
python -m src.main --test
```

## Karar Verme Mantığı

Sistem şu faktörleri değerlendirir:

1. **Vade Geçme Süresi**:
   - 0-7 gün: SMS
   - 8-14 gün: IVR veya SMS
   - 15-30 gün: Call Center
   - 30+ gün: Borç Ödeme Merkezi

2. **Ödeme Alışkanlıkları**:
   - Düzenli ödeyen: Daha az agresif kanallar
   - Geç ödeyen: Daha etkili kanallar
   - Hiç ödemeyen: Yasal takip

3. **Demografik Özellikler**:
   - Yaş grubu
   - Gelir seviyesi
   - Bölge

4. **Geçmiş Başarı Oranları**:
   - Her kanal için abone bazında başarı oranı
   - Benzer profillerdeki başarı oranları

## Öğrenme Mekanizması

Sistem her tahsilat girişiminin sonucunu kaydeder:
- Başarılı tahsilat
- Başarısız tahsilat
- Kısmi ödeme
- Yanıt yok

Bu veriler kullanılarak:
- Kanal etkinlik skorları güncellenir
- Abone profil skorları yeniden hesaplanır
- Gelecek kararlar optimize edilir

## Veritabanı Şeması

- **subscribers**: Abone bilgileri ve demografik özellikler
- **invoices**: Fatura bilgileri ve durumları
- **payment_history**: Ödeme geçmişi
- **collection_actions**: Tahsilat aksiyonları ve sonuçları
- **channel_effectiveness**: Kanal etkinlik skorları

## Lisans

MIT License
