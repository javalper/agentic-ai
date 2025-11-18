# Veri Gereksinimleri Dokümanı
## Agentic AI Alacak Yönetimi Sistemi - Legacy Veritabanı Entegrasyonu

### Genel Bakış

Bu doküman, Agentic AI sisteminin müşteri legacy veritabanından ihtiyaç duyduğu veri yapısını, tablo ve kolon gereksinimlerini detaylı olarak açıklamaktadır. Sistem hem **eğitim** (geçmiş verilerle öğrenme) hem de **üretim** (günlük operasyon) aşamalarında bu verileri kullanacaktır.

---

## 1. ABONE BİLGİLERİ (Subscribers/Customers)

### Gerekli Veriler

| Alan Adı | Veri Tipi | Zorunlu | Açıklama | Örnek Değer |
|----------|-----------|---------|----------|-------------|
| **Abone Numarası** | String/Numeric | ✅ Evet | Benzersiz abone kimliği | "SUB001", "12345678" |
| **Ad Soyad** | String | ✅ Evet | Abone adı | "Ahmet Yılmaz" |
| **Telefon** | String | ✅ Evet | Cep telefonu (SMS/IVR için) | "+905551234567" |
| **E-posta** | String | ⚪ Hayır | E-posta adresi | "ahmet@example.com" |
| **Doğum Tarihi** | Date | ✅ Evet | Yaş hesabı için | "1985-05-15" |
| **Gelir Seviyesi** | String/Numeric | ⚪ Hayır | Düşük/Orta/Yüksek veya sayısal | "Orta", "5000" |
| **Bölge/İl** | String | ✅ Evet | Coğrafi bölge | "İstanbul", "Ankara" |
| **Müşteri Tipi** | String | ⚪ Hayır | Bireysel/Kurumsal | "Bireysel" |
| **Kayıt Tarihi** | Date | ⚪ Hayır | Müşteri olma tarihi | "2020-01-15" |

### Veri Dönüşümleri

**Yaş Grubu Hesaplama:**
```
Doğum Tarihi → Yaş hesapla → Yaş Grubu
- 18-30 yaş: YOUNG
- 31-50 yaş: MIDDLE
- 51-70 yaş: SENIOR
- 70+ yaş: ELDERLY
```

**Gelir Seviyesi Standardizasyonu:**
```
Eğer sayısal değer varsa:
- < 7,500 TL: LOW
- 7,500 - 20,000 TL: MEDIUM
- > 20,000 TL: HIGH

Eğer kategorik değer varsa:
- "Düşük", "Az", "Low" → LOW
- "Orta", "Medium" → MEDIUM
- "Yüksek", "High" → HIGH
```

### Legacy Veritabanı Örnek Sorgu

```sql
-- Müşteri veritabanınızdan abone bilgilerini çekmek için örnek sorgu
SELECT 
    customer_id AS subscriber_number,
    full_name AS name,
    mobile_phone AS phone,
    email,
    birth_date,
    income_level,
    city AS region,
    customer_type,
    registration_date
FROM customers
WHERE status = 'ACTIVE'
    AND mobile_phone IS NOT NULL;
```

---

## 2. FATURA BİLGİLERİ (Invoices/Bills)

### Gerekli Veriler

| Alan Adı | Veri Tipi | Zorunlu | Açıklama | Örnek Değer |
|----------|-----------|---------|----------|-------------|
| **Fatura Numarası** | String/Numeric | ✅ Evet | Benzersiz fatura kimliği | "INV-2025-001", "F123456" |
| **Abone Numarası** | String/Numeric | ✅ Evet | İlişkili abone | "SUB001" |
| **Fatura Tutarı** | Decimal | ✅ Evet | Toplam tutar (TL) | 250.50 |
| **Kesim Tarihi** | Date | ✅ Evet | Fatura kesim tarihi | "2025-10-01" |
| **Vade Tarihi** | Date | ✅ Evet | Son ödeme tarihi | "2025-10-15" |
| **Ödeme Tarihi** | Date | ⚪ Hayır | Gerçek ödeme tarihi (varsa) | "2025-10-12" |
| **Ödenen Tutar** | Decimal | ⚪ Hayır | Ödenen miktar | 250.50, 0.00 |
| **Fatura Durumu** | String | ✅ Evet | Ödendi/Ödenmedi/Kısmi | "PAID", "UNPAID", "PARTIAL" |
| **Dönem Başlangıç** | Date | ⚪ Hayır | Fatura dönemi başı | "2025-09-01" |
| **Dönem Bitiş** | Date | ⚪ Hayır | Fatura dönemi sonu | "2025-09-30" |

### Veri Dönüşümleri

**Fatura Durumu Standardizasyonu:**
```
Legacy Durum → AI Sistem Durumu
- "PAID", "Ödendi", "COMPLETED" → PAID
- "UNPAID", "Ödenmedi", "OPEN" → OVERDUE (eğer vade geçmişse)
- "PARTIAL", "Kısmi", "PART_PAID" → PARTIAL
- "PENDING", "Bekliyor" → PENDING
```

**Kalan Tutar Hesaplama:**
```
remaining_amount = invoice_amount - paid_amount
```

**Vade Geçme Hesaplama:**
```
days_overdue = TODAY - due_date (eğer pozitifse)
```

### Legacy Veritabanı Örnek Sorgu

```sql
-- Fatura veritabanınızdan fatura bilgilerini çekmek için örnek sorgu
SELECT 
    invoice_number,
    customer_id AS subscriber_number,
    total_amount AS amount,
    issue_date,
    due_date,
    payment_date,
    paid_amount,
    status AS invoice_status,
    period_start,
    period_end
FROM invoices
WHERE issue_date >= '2024-01-01'  -- Son 1-2 yıl verisi
ORDER BY issue_date DESC;
```

---

## 3. ÖDEME GEÇMİŞİ (Payment History)

### Gerekli Veriler

| Alan Adı | Veri Tipi | Zorunlu | Açıklama | Örnek Değer |
|----------|-----------|---------|----------|-------------|
| **Ödeme ID** | String/Numeric | ✅ Evet | Benzersiz ödeme kimliği | "PAY-001", "P123456" |
| **Fatura Numarası** | String/Numeric | ✅ Evet | İlişkili fatura | "INV-2025-001" |
| **Abone Numarası** | String/Numeric | ✅ Evet | İlişkili abone | "SUB001" |
| **Ödeme Tutarı** | Decimal | ✅ Evet | Ödenen miktar | 250.50 |
| **Ödeme Tarihi** | Date | ✅ Evet | Ödeme yapıldığı tarih | "2025-10-12" |
| **Ödeme Yöntemi** | String | ⚪ Hayır | Banka/Kredi Kartı/Nakit | "Banka Transferi" |
| **Vade Tarihi** | Date | ✅ Evet | Faturanın vade tarihi | "2025-10-15" |

### Veri Dönüşümleri

**Gecikme Hesaplama:**
```
days_after_due = payment_date - due_date
- Negatif: Erken ödeme (0 olarak kaydet)
- 0: Zamanında ödeme
- Pozitif: Geç ödeme
```

### Legacy Veritabanı Örnek Sorgu

```sql
-- Ödeme geçmişi sorgusu
SELECT 
    p.payment_id,
    p.invoice_number,
    p.customer_id AS subscriber_number,
    p.amount AS payment_amount,
    p.payment_date,
    p.payment_method,
    i.due_date
FROM payments p
JOIN invoices i ON p.invoice_number = i.invoice_number
WHERE p.payment_date >= '2024-01-01'
ORDER BY p.payment_date DESC;
```

---

## 4. TAHSİLAT AKSİYONLARI (Collection Actions) - OPSIYONEL

**Not:** Eğer daha önce tahsilat aksiyonları kaydedilmişse, bu veriler sistemi daha iyi eğitmek için kullanılabilir.

### Gerekli Veriler

| Alan Adı | Veri Tipi | Zorunlu | Açıklama | Örnek Değer |
|----------|-----------|---------|----------|-------------|
| **Aksiyon ID** | String/Numeric | ⚪ Hayır | Benzersiz aksiyon kimliği | "ACT-001" |
| **Fatura Numarası** | String/Numeric | ✅ Evet | İlişkili fatura | "INV-2025-001" |
| **Abone Numarası** | String/Numeric | ✅ Evet | İlişkili abone | "SUB001" |
| **Aksiyon Tipi** | String | ✅ Evet | SMS/Arama/Ziyaret | "SMS", "CALL" |
| **Aksiyon Tarihi** | Date | ✅ Evet | Aksiyon yapıldığı tarih | "2025-10-20" |
| **Sonuç** | String | ✅ Evet | Başarılı/Başarısız | "SUCCESS", "FAILED" |
| **Tahsil Edilen Tutar** | Decimal | ⚪ Hayır | Varsa tahsil edilen miktar | 250.50 |

### Veri Dönüşümleri

**Aksiyon Tipi Standardizasyonu:**
```
Legacy Aksiyon → AI Sistem Kanalı
- "SMS", "Mesaj" → SMS
- "IVR", "Otomatik Arama" → IVR
- "CALL", "Arama", "Call Center" → CALL_CENTER
- "Legal", "Yasal", "İcra" → DEBT_COLLECTION_CENTER
```

**Sonuç Standardizasyonu:**
```
Legacy Sonuç → AI Sistem Sonucu
- "SUCCESS", "Başarılı", "PAID" → SUCCESS
- "PARTIAL", "Kısmi" → PARTIAL_SUCCESS
- "FAILED", "Başarısız" → FAILED
- "NO_ANSWER", "Cevap Yok" → NO_RESPONSE
```

### Legacy Veritabanı Örnek Sorgu

```sql
-- Tahsilat aksiyonları sorgusu (varsa)
SELECT 
    action_id,
    invoice_number,
    customer_id AS subscriber_number,
    action_type AS channel,
    action_date,
    result AS outcome,
    collected_amount
FROM collection_actions
WHERE action_date >= '2024-01-01'
ORDER BY action_date DESC;
```

---

## 5. VERİ İLİŞKİLERİ (Entity Relationships)

### İlişki Diyagramı

```
┌─────────────────────┐
│     SUBSCRIBERS     │
│  (Abone Bilgileri)  │
│                     │
│ • subscriber_number │◄────┐
│ • name              │     │
│ • phone             │     │
│ • birth_date        │     │
│ • region            │     │
└─────────────────────┘     │
                            │
                            │ 1:N
                            │
┌─────────────────────┐     │
│      INVOICES       │     │
│  (Fatura Bilgileri) │     │
│                     │     │
│ • invoice_number    │     │
│ • subscriber_number │─────┤
│ • amount            │     │
│ • due_date          │◄────┤
│ • status            │     │ 1:N
└─────────────────────┘     │
         │                  │
         │ 1:N              │
         │                  │
         ▼                  │
┌─────────────────────┐     │
│  PAYMENT_HISTORY    │     │
│  (Ödeme Geçmişi)    │     │
│                     │     │
│ • payment_id        │     │
│ • invoice_number    │─────┘
│ • subscriber_number │─────┘
│ • payment_date      │
│ • amount            │
└─────────────────────┘

         │ 1:N (opsiyonel)
         │
         ▼
┌─────────────────────┐
│ COLLECTION_ACTIONS  │
│ (Tahsilat Aksiyonları)│
│                     │
│ • action_id         │
│ • invoice_number    │
│ • channel           │
│ • outcome           │
└─────────────────────┘
```

### Birincil Anahtarlar (Primary Keys)

- **Subscribers**: `subscriber_number` (benzersiz)
- **Invoices**: `invoice_number` (benzersiz)
- **Payment_History**: `payment_id` (benzersiz)
- **Collection_Actions**: `action_id` (benzersiz)

### Yabancı Anahtarlar (Foreign Keys)

- **Invoices.subscriber_number** → **Subscribers.subscriber_number**
- **Payment_History.invoice_number** → **Invoices.invoice_number**
- **Payment_History.subscriber_number** → **Subscribers.subscriber_number**
- **Collection_Actions.invoice_number** → **Invoices.invoice_number**
- **Collection_Actions.subscriber_number** → **Subscribers.subscriber_number**

---

## 6. VERİ KALİTESİ GEREKSİNİMLERİ

### Zorunlu Kontroller

1. **Veri Bütünlüğü**
   - Her faturanın geçerli bir abone numarası olmalı
   - Her ödemenin geçerli bir fatura numarası olmalı
   - Tarih alanları geçerli format olmalı (YYYY-MM-DD)

2. **Veri Tutarlılığı**
   - Ödenen tutar, fatura tutarını geçmemeli
   - Ödeme tarihi, fatura kesim tarihinden önce olmamalı
   - Telefon numaraları geçerli format olmalı (+90XXXXXXXXXX)

3. **Eksik Veri Yönetimi**
   - Zorunlu alanlar NULL olmamalı
   - Telefon numarası olmayan aboneler hariç tutulmalı
   - Gelir seviyesi bilinmiyorsa "MEDIUM" varsayılabilir

### Veri Temizleme Önerileri

```sql
-- Geçersiz kayıtları tespit etme
SELECT 
    'Missing Phone' AS issue,
    COUNT(*) AS count
FROM customers
WHERE mobile_phone IS NULL OR mobile_phone = '';

SELECT 
    'Invalid Amount' AS issue,
    COUNT(*) AS count
FROM invoices
WHERE total_amount <= 0;

SELECT 
    'Orphan Invoice' AS issue,
    COUNT(*) AS count
FROM invoices i
LEFT JOIN customers c ON i.customer_id = c.customer_id
WHERE c.customer_id IS NULL;
```

---

## 7. VERİ HACMI VE PERFORMANS

### Beklenen Veri Miktarları

| Tablo | Minimum Kayıt | Önerilen Kayıt | Açıklama |
|-------|---------------|----------------|----------|
| **Subscribers** | 1,000 | 10,000+ | Aktif abone sayısı |
| **Invoices** | 12,000 | 120,000+ | Son 1-2 yıl fatura (aylık × abone) |
| **Payment_History** | 10,000 | 100,000+ | Ödeme kayıtları |
| **Collection_Actions** | 0 | 10,000+ | Varsa tahsilat aksiyonları |

### Eğitim İçin Önerilen Veri Aralığı

**Minimum Eğitim Verisi:**
- Son 12 ay fatura ve ödeme verileri
- En az 1,000 farklı abone
- En az 10,000 fatura kaydı

**Optimal Eğitim Verisi:**
- Son 24 ay fatura ve ödeme verileri
- 10,000+ farklı abone
- 100,000+ fatura kaydı
- Varsa tahsilat aksiyon geçmişi

---

## 8. VERİ AKTARIM FORMATI

### Seçenek 1: CSV Dosyaları (Önerilen)

**Dosya Yapısı:**
```
data_export/
├── subscribers.csv
├── invoices.csv
├── payment_history.csv
└── collection_actions.csv (opsiyonel)
```

**CSV Format Özellikleri:**
- Encoding: UTF-8
- Delimiter: Virgül (,) veya Noktalı virgül (;)
- Text Qualifier: Çift tırnak (")
- Date Format: YYYY-MM-DD
- Decimal Separator: Nokta (.)
- Header Row: Evet (ilk satır kolon isimleri)

**Örnek subscribers.csv:**
```csv
subscriber_number,name,phone,email,birth_date,income_level,region
SUB001,Ahmet Yılmaz,+905551234567,ahmet@example.com,1985-05-15,MEDIUM,İstanbul
SUB002,Ayşe Demir,+905559876543,ayse@example.com,1992-08-20,LOW,Ankara
```

### Seçenek 2: SQL Dump

```sql
-- subscribers.sql
INSERT INTO subscribers (subscriber_number, name, phone, ...) VALUES
('SUB001', 'Ahmet Yılmaz', '+905551234567', ...),
('SUB002', 'Ayşe Demir', '+905559876543', ...);
```

### Seçenek 3: JSON Format

```json
{
  "subscribers": [
    {
      "subscriber_number": "SUB001",
      "name": "Ahmet Yılmaz",
      "phone": "+905551234567",
      "birth_date": "1985-05-15",
      "region": "İstanbul"
    }
  ]
}
```

### Seçenek 4: Doğrudan Veritabanı Bağlantısı

**Gerekli Bilgiler:**
- Veritabanı Tipi: (PostgreSQL, MySQL, Oracle, SQL Server, vb.)
- Host/IP: 
- Port: 
- Database Name: 
- Schema: 
- Read-Only User Credentials:
  - Username: 
  - Password: 

**Güvenlik Notu:** Sadece okuma (SELECT) yetkisi olan bir kullanıcı oluşturulmalıdır.

---

## 9. VERİ GÜVENLİĞİ VE KVKK

### Veri Anonimleştirme (Opsiyonel)

Eğer test/geliştirme ortamı için veri sağlanacaksa, hassas bilgiler anonimleştirilebilir:

```sql
-- Anonimleştirme örneği
SELECT 
    customer_id AS subscriber_number,
    'Abone_' || customer_id AS name,  -- Gerçek isim yerine
    '+9055512' || LPAD(customer_id::text, 5, '0') AS phone,  -- Sahte telefon
    MD5(email) || '@example.com' AS email,  -- Anonimleştirilmiş email
    birth_date,
    income_level,
    city AS region
FROM customers;
```

### Veri Güvenliği Önlemleri

1. **Şifreleme**: Veri aktarımı SSL/TLS ile yapılmalı
2. **Erişim Kontrolü**: Sadece yetkili personel erişebilmeli
3. **Audit Log**: Veri erişimleri loglanmalı
4. **Veri Saklama**: Veriler güvenli ortamda saklanmalı
5. **Veri Silme**: Proje sonrası veriler silinmeli (KVKK)

---

## 10. VERİ DOĞRULAMA VE TEST

### Veri Doğrulama Checklist

- [ ] Tüm zorunlu alanlar dolu mu?
- [ ] Tarih formatları doğru mu?
- [ ] Sayısal değerler geçerli mi?
- [ ] İlişkiler (foreign keys) tutarlı mı?
- [ ] Telefon numaraları geçerli format mı?
- [ ] Aynı abone için birden fazla fatura var mı?
- [ ] Ödeme tutarları fatura tutarlarıyla uyumlu mu?
- [ ] Vade geçmiş faturalar doğru işaretlenmiş mi?

### Test Verisi Önerisi

İlk aşamada **küçük bir test verisi** sağlanması önerilir:
- 100 abone
- 1,000 fatura
- 800 ödeme kaydı

Bu test verisiyle:
1. Veri formatı doğrulanır
2. Entegrasyon test edilir
3. İlk sonuçlar değerlendirilir
4. Sorunlar tespit edilir

---

## 11. ENTEGRASYON SÜRECİ

### Adım 1: Veri Analizi (1 hafta)
- Legacy veritabanı yapısı incelenir
- Veri kalitesi değerlendirilir
- Mapping (eşleştirme) planı oluşturulur

### Adım 2: Test Verisi (1 hafta)
- Küçük test verisi alınır
- Veri dönüşüm scriptleri yazılır
- İlk import test edilir

### Adım 3: Tam Veri İmport (1 hafta)
- Tüm geçmiş veri alınır
- AI sisteme yüklenir
- Veri doğrulama yapılır

### Adım 4: Eğitim (1-2 hafta)
- Sistem geçmiş verilerle eğitilir
- Model performansı değerlendirilir
- Parametreler optimize edilir

### Adım 5: Pilot Uygulama (2-4 hafta)
- Küçük bir segment ile test
- Sonuçlar izlenir
- İyileştirmeler yapılır

---

## 12. DESTEK VE İLETİŞİM

### Veri Sağlama Süreci İçin İletişim

**Teknik Sorular:**
- Veritabanı şeması
- Veri formatları
- Entegrasyon detayları

**İş Sorular:**
- Veri kapsamı
- Zaman aralığı
- Güvenlik gereksinimleri

### Gerekli Dokümanlar

Lütfen aşağıdaki dokümanları sağlayın:
- [ ] Veritabanı şema diyagramı (ERD)
- [ ] Tablo ve kolon açıklamaları (data dictionary)
- [ ] Örnek veri (10-20 kayıt)
- [ ] Veri hacmi bilgisi (kayıt sayıları)
- [ ] Veri güvenliği politikaları

---

## ÖZET: MÜŞTERİYE SORULACAK SORULAR

### Kritik Sorular

1. **Veritabanı Yapısı**
   - Hangi veritabanı sistemi kullanılıyor? (PostgreSQL, Oracle, SQL Server, vb.)
   - Abone bilgileri hangi tabloda? Kolon isimleri neler?
   - Fatura bilgileri hangi tabloda? Kolon isimleri neler?
   - Ödeme geçmişi hangi tabloda? Kolon isimleri neler?

2. **Veri Kapsamı**
   - Kaç aktif abone var?
   - Aylık ortalama kaç fatura kesiliyor?
   - Ne kadar geçmiş veri mevcut? (1 yıl, 2 yıl, 5 yıl?)
   - Tahsilat aksiyon geçmişi var mı?

3. **Veri Kalitesi**
   - Tüm abonelerin telefon numarası var mı?
   - Doğum tarihi bilgisi eksiksiz mi?
   - Ödeme kayıtları düzenli tutuluyor mu?
   - Veri temizliği yapılmış mı?

4. **Veri Erişimi**
   - Veriyi nasıl sağlayabilirsiniz? (CSV, SQL dump, DB bağlantısı)
   - Doğrudan veritabanı erişimi verilebilir mi?
   - Veri güvenliği gereksinimleri neler?
   - KVKK uyumluluğu için özel gereksinim var mı?

5. **Zaman Çizelgesi**
   - Veri ne zaman sağlanabilir?
   - Test verisi önce sağlanabilir mi?
   - Veri güncellemeleri ne sıklıkta yapılacak?

---

**Hazırlayan:** Agentic AI Geliştirme Ekibi  
**Tarih:** 18 Kasım 2025  
**Versiyon:** 1.0
