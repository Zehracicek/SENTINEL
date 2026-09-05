# SENTİNEL — Astrobiyolojik Sensör Yükü Veri Mimarisi

> NASA **SMAP/MSL Anomaly Detection** veri setindeki MSL (Curiosity) kanallarından gelen telemetriyi **sıralı replay** ile üreten; uçta (edge) anomali skoru, öncelik, sıkıştırma ve **uplink kuyruğu** ile işleyen; PostgreSQL + WebSocket üzerinden ground station dashboard’unda canlı gösteren web uygulaması. Skor **z-score + River** hibritidir; `smoothed_errors/*.npy` varsa LSTM hata sinyali de karışır. Çalışma zamanında **TensorFlow/Keras veya `.h5` yükleme yoktur**. İsteğe bağlı [NASA Open API](https://api.nasa.gov/) proxy’si (`/api/nasa/*`) **NASA_ARŞİV** sayfasında APOD ve Curiosity fotoğraflarını gösterir — bu, replay telemetrisi değildir.

---

## 1. Proje Özeti

Bu proje, **NASA SMAP/MSL Anomaly Detection veri setindeki** MSL (Curiosity) telemetrisini **dosyadan sıralı replay** ederek şu süreçleri modellemek için kullanır:

1. **Veri toplama** — 12 MSL kanalından normalize edilmiş telemetri okuması
2. **Edge tamponlama** — Ring buffer ile dairesel veri depolama (500 okuma/kanal)
3. **Anomali tespiti** — Kanal bazlı z-score + River; `smoothed_errors/*.npy` varsa LSTM hata sinyali + River (`GET /health` → `anomaly_score_source`)
4. **Bilimsel önceliklendirme** — Organik molekül (10/10) → Sıcaklık ekstremi (4/10)
5. **Bant optimizasyonu** — Skor eşiğine göre paket filtreleme + uplink yükü için **delta kodlama + zlib (DEFLATE)** ile gerçek ikili sıkıştırma (`compressor.py`)
6. **DSN iletimi + uplink kuyruğu** — Yüksek öncelikli okumalar `uplink_queue` tablosunda bekletilir; `uplink_drain_loop` periyodik olarak sınırlı sayıda paket “gönderilir” ve WebSocket ile güncellenir
7. **Ground station dashboard** — Gerçek zamanlı WebSocket ile canlı gösterim
8. **VERİ_AKIŞI ekranı** — 8 adımlı uçtan uca pipeline animasyonu (ayarlanabilir hız, ilerleme çubuğu, canlı `stats_update` metrikleri)

Bu liste, hackathon konusuyla uyumlu **uçtan uca edge + ground station** akışının yazılım prototipidir; canlı Mars bağlantısı veya uçta Keras çıkarımı içermez.

**Arayüz ve API belgeleri:** React panelleri ve OpenAPI (`/docs`) etiketleri Türkçe birincil dildir; sensör tipleri, JSON alan adları ve makine okumalı uçlar (ör. `GET /health`) uluslararası kısaltmalarla uyumludur.

### 1.1 Metodoloji, şeffaflık ve veri modeli

**Edge kararı ve ground truth**  
NASA veri setindeki etiketli anomali bölgeleri (`labeled_anomalies.csv`) simülatörde okunur ve her kayıtta `ground_truth_anomaly` alanına *yalnızca izleme / değerlendirme* için yazılır. **Edge işlemcisinde `is_anomaly` yalnızca skor tabanlıdır** (ör. eşik ≥ 50, LSTM smoothed error veya z-score türevi); veri seti etiketi karara **katılmaz** — böylece ground-truth leakage önlenir. Karşılaştırmalı analiz için DB’de hem edge çıktısı (`is_anomaly`) hem veri seti etiketi (`ground_truth_anomaly`) bir arada tutulur.

**Kanal izlenebilirliği**  
MSL kanal kimliği (`T-1`, `M-6`, `C-1`, …) `sensor_readings.channel_id` sütununda saklanır.

**Görev ve UI tutarlılığı**  
Telemetri kaynağı **MSL (Curiosity)** veri setidir. Harita ve yan metinler **Gale Krateri / Bradbury İniş** bölgesiyle uyumludur; Jezero veya Perseverance’a özgü enstrüman adları (ör. PIXL, SHERLOC) varsayılan anlatıda kullanılmaz; sensör açıklamaları REMS / SAM / ChemCam bağlamıyla hizalanır.

**VERİ_AKIŞI sayfası**  
Sekiz adımlı animasyon ve metinler **pedagojik şema / sahnelemedir**; gerçek rover uçuş yazılım yığınının birebir kopyası değildir. Sayısal metrikler mümkün olduğunca backend’deki canlı istatistiklere bağlanır.

**Veritabanı şeması**  
Tablolar **yalnızca Alembic** ile oluşturulur ve güncellenir (`alembic upgrade head`). Uygulama başlangıcında `metadata.create_all` **kullanılmaz**.

---

## 2. Veri Seti: NASA SMAP/MSL

### Kaynak
**NASA Anomaly Detection Dataset** — orijinal çalışma: *"Detecting Spacecraft Anomalies Using LSTMs and Nonparametric Dynamic Thresholding"* (Hundman et al., KDD 2018), depo: [khundman/telemanom](https://github.com/khundman/telemanom).

Erişim yolları:

| Kaynak | Durum | İçerik |
|--------|-------|--------|
| `s3-us-west-2.amazonaws.com/telemanom/data.zip` | ❌ **403 Forbidden** — kapatıldı | — |
| [Kaggle](https://www.kaggle.com/datasets/patrickfleith/nasa-anomaly-detection-dataset-smap-msl) | ✔ API anahtarı gerekir | train + test + modeller + `smoothed_errors` + `y_hat` |
| [HuggingFace `appleparan/telemanom`](https://huggingface.co/datasets/appleparan/telemanom) | ✔ Kimlik doğrulaması yok | yalnızca train + test |

`scripts/fetch_dataset.py` HuggingFace aynasını kullanır (bkz. Hızlı Başlangıç). Önceden hesaplanmış LSTM artifaktlarına ihtiyacınız varsa Kaggle paketini indirip `backend/data/2018-05-19_15.00.10/` altına yerleştirin.

### İçerik

| Özellik | Değer |
|---------|-------|
| Uzay aracı | SMAP (uydu) + MSL (Curiosity rover) |
| Toplam kanal | 82 (54 SMAP + 28 MSL) |
| Veri formatı | `.npy` (NumPy dizileri), normalize [-1, 1] |
| Anomali etiketleri | `labeled_anomalies.csv` — ground truth |
| Anomali tipleri | Point anomaly, Contextual anomaly |
| Toplam veri noktası | ~496.444 telemetri değeri |
| Anomali sekansı | 105 etiketlenmiş anomali bölgesi |

### Kullanılan MSL Kanalları

Aşağıdaki boyutlar `backend/data/test/*.npy` dosyalarından doğrulanmıştır (`numpy.load(...).shape`):

| Kanal ID | Sensör Tipi | Açıklama | Test verisi boyutu |
|----------|-------------|----------|--------------------|
| T-1 | TEMP | Sıcaklık sensörü | 8612 × 25 |
| T-2 | TEMP | Termal kontrol | 8625 × 25 |
| P-10 | PRESS | Basınç sistemi | 6100 × 55 |
| P-14 | PRESS | Hidrolik basınç | 6100 × 55 |
| M-6 | CH4 | Metan dedektörü | 2049 × 55 |
| M-7 | MOIST | Nem sensörü | 2156 × 55 |
| C-1 | SPEC | Spektrometre A | 2264 × 55 |
| C-2 | SPEC | Spektrometre B | 2051 × 55 |
| D-14 | UV | UV radyasyon | 2625 × 55 |
| D-15 | O2 | Oksijen sensörü | 2158 × 55 |
| D-16 | CO2 | CO₂ sensörü | 2191 × 55 |
| F-7 | SPEC | FTIR spektroskopi | 5054 × 55 |

> Her kanalda ilk sütun telemetri değeri, kalan sütunlar komut one-hot encoding'leridir. Simülatör yalnızca ilk sütunu okur (`data[idx, 0]`).

> Telemetri **çoğunlukla** [-1, 1] aralığında normalize edilmiştir, ancak veri setinde uç değerler vardır: `M-6` ilk sütununda 258.1'e kadar çıkan gerçek örnekler bulunur. Bu, z-score yolunda beklenen biçimde yüksek anomali skoru üretir.

### Önceden Eğitilmiş LSTM Modeli (veri seti dosyaları)

**Çalışma zamanı:** Uygulama yalnızca `smoothed_errors/*.npy` (ve gerekirse z-score) kullanır; `.h5` dosyaları repoda **araştırma / eğitim mirası** olarak durur, backend bunları **yükleyip çıkarım yapmaz**.

Veri seti içinde eğitilmiş LSTM modeli ve türev çıktılar bulunur:

| Dosya | Açıklama |
|-------|----------|
| `models/*.h5` | Her kanal için eğitilmiş Keras LSTM modeli |
| `y_hat/*.npy` | LSTM tahmin çıktıları (beklenen değerler) |
| `smoothed_errors/*.npy` | Düzeltilmiş hata skorları (anomali göstergesi) |
| `params.log` | Model hiperparametreleri ve performans metrikleri |

#### LSTM Model Parametreleri

```
Katmanlar:        2 × LSTM (80 birim)
Batch size:       70
Epochs:           35
Dropout:          0.3
Optimizer:        Adam
Loss:             MSE (Mean Squared Error)
Sequence length:  250
Window size:      30
Smoothing:        %5
Validation split: %20
```

#### Referans model performansı — *bu projenin sonucu değildir*

Aşağıdaki rakamlar **Hundman et al. (KDD 2018)** çalışmasının kendi LSTM + nonparametrik eşikleme boru hattına aittir ve veri setiyle birlikte dağıtılan `params.log` çıktısından gelir. Bu depodaki edge işlemcisinin başarısını **temsil etmez**:

| Uzay aracı | Precision | Recall | F_0.5 |
|-----------|-----------|--------|-------|
| SMAP | %85.5 | %85.5 | 0.71 |
| Curiosity (MSL) | %92.6 | %69.4 | 0.69 |
| Toplam (82 kanal) | %87.5 | %80.0 | 0.71 |

#### Bu sistemin kendi ölçümü

Edge kararı (`sensor_readings.is_anomaly`) yalnızca skor tabanlıdır; veri seti etiketi (`ground_truth_anomaly`) karara katılmaz, yalnızca değerlendirme için saklanır. İkisinin karşılaştırması canlı olarak şu uçtan alınır:

```bash
curl http://localhost:8000/api/evaluation/detection
curl "http://localhost:8000/api/evaluation/detection?sensor_type=CH4"
```

Yanıt nokta metriklerinin yanı sıra Hundman örtüşmeli dizi metriklerini (`sequence_precision`, `sequence_recall`, `sequence_f1_score`) de döndürür; `replay_index` yoksa dizi alanları boş kalır. `anomaly_score_source` skorun LSTM mi z-score mu olduğunu bildirir.

Sunucuyu saatlerce çalıştırmadan aynı ölçümü çevrimdışı almak için:

```bash
python scripts/score_sanity_check.py --steps 3000
```

#### Ölçülen sonuçlar (36.000 okuma, z-score + River yolu)

Gerçek etiketli anomali oranı bu örneklemde **%10.18**. Eşik taraması:

| Eşik | İşaretlenen | TP | FP | Precision | Recall | F1 |
|------|-------------|----|----|-----------|--------|-----|
| 40 (batarya dolu, RL −5) | %45.4 | 2572 | 13788 | 0.157 | 0.702 | 0.257 |
| **50** (varsayılan taban) | **%28.3** | 1731 | 8457 | 0.170 | 0.472 | 0.250 |
| 60 (batarya %20–50) | %12.4 | 1009 | 3445 | 0.227 | 0.275 | 0.249 |
| 70 (batarya < %20) | %6.6 | 724 | 1643 | 0.306 | 0.198 | 0.240 |
| 85 (üst sınır) | %1.2 | 257 | 188 | 0.578 | 0.070 | 0.125 |

**Dürüst değerlendirme:** LSTM `smoothed_errors` artifaktları olmadan bu boru hattı zayıf bir dedektördür — F1 tüm eşik bandı boyunca 0.24–0.26 arasında sıkışır, yani eşik seçimi precision ile recall arasında takas yapmaktan öteye gitmez. Makalenin F_0.5 = 0.69 sonucu eğitilmiş LSTM tahmin hatası + nonparametrik dinamik eşikleme ile elde edilmiştir; z-score + HalfSpaceTrees harmanı bunun yerine geçemez.

Bu projenin asıl gösterdiği şey **uçtan buluta veri azaltma mimarisi**dir (kademeli filtreleme, delta + DEFLATE sıkıştırma, öncelikli uplink kuyruğu, enerji duyarlı eşik, RL geri beslemesi) — en iyi anomali tespit doğruluğu değil. Tespit kalitesini artırmak için `smoothed_errors` artifaktlarını Kaggle paketinden ekleyin.

---

## 3. Sistem Mimarisi

```
KATMAN 1 — SENSOR LAYER
  MSL .npy replay (12 kanal) ─────────────────────────────────────────────┐
                                                                          │
KATMAN 2 — ROVER / EDGE 1                                                 ▼
  ┌──────────────────────────────────────────────────────────────────────┐
  │ Ring buffer (500/kanal) · LSTM/z + River HalfSpaceTrees hibrit skor │
  │ Novelty (cosine, son 1000 vektör) · is_novel → öncelik +2           │
  │ EnergyController: batarya simülasyonu → eşik + zlib seviyesi      │
  │ RLAgent (Q-tablo ε-greedy) → eşik ince ayarı · pickle kalıcılık     │
  │ Filtre: skor < eşik DROP · skor ≥ eşik → uplink_queue + orbiter_queue│
  │ Delta + zlib DEFLATE (uplink drain anında)                           │
  └───────────────────────────────┬──────────────────────────────────────┘
                                  │ DSN uplink (10s) · orbiter drain (15s)
                                  ▼
KATMAN 3 — ORBITER / EDGE 2
  ┌──────────────────────────────────────────────────────────────────────┐
  │ orbiter_queue → skor < 40 DROP · 30 sn batch pencere                │
  │ relay_latency_ms, pass_id · orbiter_relay_log · WS orbiter_stats    │
  └───────────────────────────────┬──────────────────────────────────────┘
                                  │ (simüle downlink)
                                  ▼
KATMAN 4 — EARTH / CLOUD (simüle)
  ┌──────────────────────────────────────────────────────────────────────┐
  │ Her 20 orbiter batch’te model_updates (eşik önerisi, federated round)│
  │ RL epsilon geri beslemesi · WS model_update                          │
  └───────────────────────────────┬──────────────────────────────────────┘
                                  ▼
GROUND STATION (FastAPI + PostgreSQL + WebSocket + React)
  sensor_readings · anomaly_events · transmission_log · uplink_queue ·
  orbiter_queue · orbiter_relay_log · model_updates · NASA proxy
```

---

## 4. Algoritmalar — Adım Adım

### Adım 1: Veri Toplama (`simulator.py`)

NASA MSL test verisi `.npy` dosyalarından sıralı olarak okunur. Her turda 12 kanaldan birer okuma alınır; tur aralığı varsayılan **10 saniyedir** (`SENTINEL_SIM_INTERVAL_SECONDS` ile 1–120 sn arası ayarlanabilir).

```python
raw_value = float(channel_data[cursor, 0])  # İlk sütun = telemetri
cursor += 1  # Sıralı replay
```

Aynı anda `labeled_anomalies.csv`'den o timestep'in gerçek anomali olup olmadığı kontrol edilir. Bu ground truth, edge processor'un doğruluğunu ölçmek için kullanılır.

### Adım 2: Edge Tamponlama

Her sensör tipi için son 500 okuma ring buffer'da tutulur. Bu buffer, z-score hesaplaması için istatistiksel referans sağlar.

### Adım 3: Anomali Skoru Hesaplama (`edge_processor.py`)

Skor **iki sinyalin ağırlıklı ortalamasıdır**; hiçbiri tek başına belirleyici değildir.

#### Taban sinyal A: LSTM Smoothed Error

Veri setinde önceden hesaplanmış `smoothed_errors/*.npy` dosyaları **varsa** kullanılır (Keras çalıştırılmaz):

```
lstm_skoru = min(100, smoothed_error × 300)
```

#### Taban sinyal B: Z-Score (smoothed error yoksa)

```
z_score = |değer - ortalama| / standart_sapma      # kanal başına son 500 okuma
z_skoru = min(100, z_score × 25)
```

#### Harmanlama: River HalfSpaceTrees

Her okuma ayrıca çevrimiçi bir `HalfSpaceTrees` modeline verilir (`river_learner.py`) ve nihai skor şu şekilde birleştirilir:

```
smoothed error varsa:  skor = 0.50 × lstm_skoru + 0.50 × river_skoru
smoothed error yoksa:  skor = 0.40 × z_skoru    + 0.60 × river_skoru
```

> **Önemli:** `smoothed_errors/` klasörü yalnızca veri setinin Kaggle paketinde bulunur. Yalnızca `train/`+`test/` indirildiyse sistem z-score + River yolunda çalışır. Hangi yolun etkin olduğunu `GET /health` içindeki `dataset.anomaly_score_source` alanı bildirir.

### Adım 4: Karar Motoru — tek dinamik eşik

Kodda üç kademeli bir sınıflandırma **yoktur**; tek bir eşik hem anomali etiketini hem iletim kararını belirler:

```python
is_anomaly        = skor >= esik
uplink_eligible   = skor >= esik      # aynı koşul
```

Eşik sabit 50 değildir; batarya durumuna ve RL düzeltmesine göre **40–85** arasında hareket eder:

| Batarya | Taban eşik | zlib seviyesi |
|---------|-----------|---------------|
| < %20 | 70 | 9 |
| %20 — %50 | 60 | 7 |
| > %50 | 50 | 6 |

RL ajanı (`rl_agent.py`) bu tabana −5 / 0 / +5 ekler; sonuç `max(40, min(85, ...))` ile sınırlanır. Skoru eşiğin altında kalan okumalar iletilmez (DROP), üstünde kalanlar `uplink_queue` ve `orbiter_queue` tablolarına yazılır.

### Adım 5: Anomali Sınıflandırma

Tespit edilen anomaliler bilimsel önemlerine göre sınıflandırılır:

| Anomali Tipi | Tetikleyen Sensör | Bilimsel Öncelik |
|-------------|-------------------|-----------------|
| Organik Molekül İmzası | 3+ sensör aynı anda anomali | 10/10 |
| Metan Spike | CH4 (M-6) | 8/10 |
| Spektral Sapma | SPEC (C-1, C-2, F-7) | 7/10 |
| Nem Anomalisi | MOIST (M-7) | 6/10 |
| Radyasyon Anomalisi | UV (D-14) | 5/10 |
| Atmosferik Anomali | O2, CO2 (D-15, D-16) | 5/10 |
| Basınç Anomalisi | PRESS (P-10, P-14) | 4/10 |
| Sıcaklık Ekstremi | TEMP (T-1, T-2) | 4/10 |

### Adım 6: Bant Genişliği Optimizasyonu + İkili Sıkıştırma (`compressor.py`)

**Filtreleme:** Skor ≥ 50 olan okumalar `is_transmitted=True` ile işaretlenir; düşük skorlular iletilmez. Paket başına **256 byte** varsayımıyla filtre tasarrufu hesaplanır:

```
tasarruf_filtre = (1 - iletilen_paket / toplam_paket) × 100
```

**Sıkıştırma (gerçek codec):** Her batch’te yalnızca iletilecek kayıtlar üzerinde:

1. `raw_value` ve `anomaly_score` çiftleri **little-endian float64** olarak ardışık paketlenir.
2. **Delta kodlama:** İlk değer aynen kalır; sonraki örnekler bir öncekine göre fark olarak yazılır (düz telemetride entropi azalır).
3. **zlib.compress(level=6)** — DEFLATE tabanlı sıkıştırma (standart kütüphane; uzay telemetrisinde kullanılan Rice/Huffman tarzı kayıpsız kodlamanın karşılığı olarak düşünülebilir).

`edge_processor.process_batch` bu yükü üretir; `get_stats()` ve WebSocket `stats_update` ile birlikte şu alanlar yayınlanır:

| Alan | Anlamı |
|------|--------|
| `payload_serialized_bytes` | Uplink için paketlenmiş ham byte (kümülatif) |
| `payload_deflated_bytes` | zlib sonrası byte (kümülatif) |
| `payload_deflate_ratio` | sıkıştırılmış / ham (0–1) |
| `payload_deflate_savings_percent` | (1 − oran) × 100 |
| `last_batch_payload_bytes` / `last_batch_deflated_bytes` | Son batch özet |

> Veritabanındaki `transmission_log.compression_ratio` sütunu **paket iletim oranını** (iletilen / toplam) ifade eder; DEFLATE oranı yalnızca API/WebSocket istatistiklerindedir.

### Adım 7: Dashboard Gösterimi

İletilen veriler WebSocket üzerinden React dashboard'a aktarılır:

```json
{"type": "sensor_reading", "data": {...}}       // Simülasyon veya uplink’ten gelen okuma
{"type": "anomaly_alert", "data": {...}}        // Anomali tespiti
{"type": "stats_update", "data": {...}}         // ~5 s: DB özet + edge istatistikleri + rover + uplink_queue
{"type": "uplink_queue_update", "data": {...}}  // Kuyruk drain sonrası güncel snapshot
{"type": "orbiter_stats", "data": {...}}        // Orbiter Edge2 özet metrikleri
{"type": "model_update", "data": {...}}         // Earth/Cloud model önerisi (federated)
// stats_update içi: river_stats, energy_stats, rl_stats (ayrıca tek başına energy_stats / rl_stats WS ile de gelebilir)
```

---

## 5. Teknoloji Stack

| Katman | Teknoloji | Kullanım |
|--------|-----------|----------|
| Backend | Python 3.11+, FastAPI | REST API + WebSocket |
| HTTP istemcisi | httpx | NASA Open API proxy (`/api/nasa/*`) |
| ORM | SQLAlchemy (async) | PostgreSQL bağlantısı |
| Veritabanı | PostgreSQL 16 | Zaman serisi depolama |
| Migration | Alembic | Şema yönetimi |
| Veri İşleme | NumPy, Pandas | NASA .npy okuma, istatistik |
| Anomali sinyali | LSTM pipeline çıktısı (`.npy`) | `smoothed_errors`; `.h5` yalnızca veri setinde, runtime’da yok |
| Frontend | React 18, Vite | SPA dashboard |
| Grafik | Recharts | Zaman serisi görselleştirme |
| Stil | Tailwind CSS | Cyberpunk neon tema |
| Konteyner | Docker Compose | PostgreSQL |

---

## 6. API Endpoints

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/health` | Sağlık kontrolü + veri seti durumu (`dataset.ready`, `anomaly_score_source`) |
| GET | `/api/sensor-data` | Son okumalar (`skip`, `limit`, isteğe bağlı `sensor_type`) |
| GET | `/api/sensor-data/stats` | Sensör tipi istatistikleri |
| GET | `/api/sensor-data/{id}` | Tek okuma detayı (UUID) |
| POST 🔒 | `/api/sensor-data/simulate` | Manuel simülasyon batch’i (paylaşılan işlemciyi kullanır) |
| GET | `/api/anomalies` | Anomali listesi (`severity`, `acknowledged`, sayfalama); `sensor_type` ve `channel_id` alanlarını da döner |
| GET | `/api/anomalies/recent` | Son 10 anomali |
| GET | `/api/anomalies/stats` | Anomali tipi dağılımı |
| GET | `/api/anomalies/{id}/detail` | İlişkili sensör okuması ile anomali detayı |
| PATCH 🔒 | `/api/anomalies/{id}/acknowledge` | Anomaliyi onayla |
| GET | `/api/evaluation/detection` | Nokta + Hundman dizi precision/recall/F1 (`sensor_type` ile filtrelenebilir) |
| GET | `/api/uplink-queue` | Uplink kuyruğu anlık görünümü (snapshot) |
| GET | `/api/nasa/apod` | APOD proxy (`date` isteğe bağlı); `NASA_API_KEY` gerekir |
| GET | `/api/nasa/mars-photos/{rover}` | Mars fotoğrafları (`earth_date` veya `sol`, `camera`, `page`) |
| GET | `/api/nasa/mars-photos-recent/{rover}` | Manifest’ten en güncel sol’lara göre son N fotoğraf (`limit`) |
| GET | `/api/orbiter-log` | Orbiter relay log kayıtları |
| GET | `/api/model-updates` | Earth/Cloud simülasyonu `model_updates` geçmişi |
| GET | `/api/settings/rover-thinking` | Groq düşünce modu açık/kapalı |
| PATCH 🔒 | `/api/settings/rover-thinking` | Gövde: `{"enabled": true}` veya `false` — düşünce çağrılarını durdur/başlat |
| WS | `/ws/live-feed` | Gerçek zamanlı akış (aşağıdaki mesaj tipleri) |

🔒 = `X-API-Token` başlığı gerekir; değer `backend/.env` içindeki `SENTINEL_API_TOKEN`'dır. Panel düğmeleri (`ONAYLA`, rover düşünce) aynı değeri `frontend/.env` içinde `VITE_API_TOKEN` olarak ister; Vite yeniden başlatılmalıdır. Anahtar tanımlı değilse bu uçlar 503 ile kapalıdır — açık bir sunucuda kimliksiz yazma veya Groq harcaması tetiklenemez. Okuma uçları ve WebSocket akışı korumasızdır.

```bash
curl -X PATCH http://localhost:8000/api/settings/rover-thinking \
  -H "X-API-Token: $SENTINEL_API_TOKEN" \
  -H "Content-Type: application/json" -d '{"enabled": false}'
```

---

## 7. Dashboard Sayfaları

Sayfalar **React Router** ile yönetilir. **Ana sayfa** (`/`) 3D veri akışı özeti ve yapay zekâ bölümü içerir; **operasyon paneli** `/gosterge_paneli` ve diğer yollar altındadır. Doğrudan URL veya yenilemede nginx’in `try_files $uri $uri/ /index.html;` kullanması gerekir — örnek: `nginx-spa-fragment.conf`.

| Sayfa | URL yolu | İçerik |
|-------|----------|--------|
| ANA_SAYFA | `/` | Yumuşak tema, 3D uçtan uca akış şeması, AI analiz/eğitim özeti; panele geçiş bağlantıları |
| GÖSTERGE_PANELİ | `/gosterge_paneli` | Metrik kartları, anomali grafiği, bant göstergesi, ham veri akışı tablosu (sütunlarda kanal, TX = iletilmiş) |
| VERİ_AKIŞI | `/veri_akisi` | 8 adım: pedagojik pipeline (canvas animasyon, hız, ilerleme); canlı `stats_update` metrikleri |
| ANOMALİ_TESPİT | `/anomali_tespit` | Alarm merkezi — severity filtre, onaylama, detay |
| SENSÖR_DETAY | `/sensor_detay` | Sensör bazlı özet ve anomali bağlamı |
| TELEMETRİ | `/telemetri` | Canlı telemetri görünümü |
| ROVER_HARİTA | `/rover_harita` | Rover konum / harita bağlamı |
| İLETİM_ANALİZİ | `/iletim_analizi` | Paket iletimi, bant tasarrufu, delta + DEFLATE özeti |
| UPLINK_KUYRUĞU | `/uplink_kuyrugu` | Bekleyen / gönderilen uplink kuyruğu (`stats.uplink_queue`) |
| ORBITER_RÖLE | `/orbiter_role` | Orbiter Edge2: kuyruk, 30 sn pencere, düşük skor (eşik 40) paket düşürme, `orbiter_stats` |
| YER_İSTASYONU_BULUT | `/yer_istasyonu_bulut` | Earth/Cloud: 20 relay batch sonrası `model_update`, RL epsilon geri beslemesi |
| VERİ_SETİ | `/veri_seti` | Veri seti bilgi paneli |
| ROVER_ZEKASİ | `/rover_zekasi` | Groq rover düşünce akışı (`rover_thinking` WS) |

---

## 8. Veritabanı Şeması

### sensor_readings
| Sütun | Tip | Açıklama |
|-------|-----|----------|
| id | UUID | Primary key |
| sensor_type | VARCHAR(10) | TEMP, CH4, O2, CO2, MOIST, SPEC, UV, PRESS |
| channel_id | VARCHAR(20) | MSL kanal kimliği (örn. T-1, M-6); izlenebilirlik |
| raw_value | FLOAT | Normalize telemetri değeri [-1, 1] |
| unit | VARCHAR(20) | Ölçü birimi |
| anomaly_score | FLOAT | 0-100 arası hesaplanan skor |
| is_anomaly | BOOLEAN | Edge kararı (yalnızca skor tabanlı; etiket sızması yok) |
| ground_truth_anomaly | BOOLEAN | Veri seti etiketi (değerlendirme; edge kararına dahil değil) |
| is_transmitted | BOOLEAN | DSN üzerinden iletildi mi |
| location_lat | FLOAT | Rover Mars koordinatı |
| location_lon | FLOAT | Rover Mars koordinatı |
| sol | INTEGER | Mars günü sayacı |
| created_at | TIMESTAMPTZ | Oluşturulma zamanı |

### anomaly_events
| Sütun | Tip | Açıklama |
|-------|-----|----------|
| id | UUID | Primary key |
| reading_id | UUID | FK → sensor_readings |
| anomaly_type | VARCHAR(30) | organic_molecule, methane_spike, vb. |
| severity | VARCHAR(10) | CRITICAL, HIGH, MEDIUM, LOW |
| description | TEXT | Türkçe anomali açıklaması |
| scientific_priority | INTEGER | 1-10 bilimsel öncelik |
| acknowledged | BOOLEAN | Bilim insanı onayı |
| created_at | TIMESTAMPTZ | Tespit zamanı |

### transmission_log
| Sütun | Tip | Açıklama |
|-------|-----|----------|
| id | UUID | Primary key |
| batch_id | UUID | İletim grubu |
| total_packets | INTEGER | Toplam paket |
| transmitted_packets | INTEGER | İletilen paket |
| bytes_saved | BIGINT | Tasarruf edilen byte |
| compression_ratio | FLOAT | Paket iletim oranı (iletilen / toplam); DEFLATE oranı değildir |
| transmission_window | VARCHAR(50) | DSN istasyonu |
| created_at | TIMESTAMPTZ | İletim zamanı |

---

## 9. Hızlı Başlangıç

### 1. Ortam değişkenleri

Repoda hiçbir parola tutulmaz; iki `.env` dosyası oluşturmanız gerekir.

**Kök `.env`** (docker-compose için, şablon: `.env.example`):

```bash
cp .env.example .env        # POSTGRES_PASSWORD değerini kendiniz belirleyin
```

**`backend/.env`** (şablon: `backend/.env.example`):

| Değişken | Zorunlu | Açıklama |
|----------|---------|----------|
| `DATABASE_URL` | ✔ | Async sürücü (`postgresql+asyncpg://...`). Tanımsızsa uygulama açılışta hata verir. |
| `DATABASE_URL_SYNC` | — | Alembic senkron sürücü ister. Boşsa `DATABASE_URL` otomatik çevrilir. |
| `SENTINEL_API_TOKEN` | — | Yazma yapan uçları (`POST`/`PATCH`) korur. **Boşsa bu uçlar 503 ile kapalıdır.** |
| `NASA_API_KEY` | — | Boşsa resmi `DEMO_KEY` (saatlik ~30). Kişisel anahtar ücretsiz: [api.nasa.gov](https://api.nasa.gov) |
| `GROQ_API_KEY` | — | Boşsa rover düşünce modu sessizce fallback'e düşer |
| `CORS_ALLOW_ORIGINS` | — | Virgüllü origin listesi; varsayılan yalnızca `localhost:5173` |
| `SENTINEL_SIM_INTERVAL_SECONDS` | — | Simülasyon turu aralığı, varsayılan **10 sn** |
| `SENTINEL_UPLINK_DRAIN_BATCH` | — | Tur başına boşaltılan uplink paketi, varsayılan 12 (kanal sayısı) |

### 2. PostgreSQL Başlat
```bash
docker compose up -d
```
Port yalnızca `127.0.0.1:5432` üzerine bağlanır; veritabanı ağdan erişilebilir olmaz.

### 3. NASA veri setini indir (zorunlu)

Veri seti repoda yer almaz. Bu adım atlanırsa uygulama **çalışır ama hiç okuma üretmez** — `GET /health` bunu `"status": "degraded"` ile bildirir.

```bash
python scripts/fetch_dataset.py            # 12 MSL kanalının test verisi
python scripts/fetch_dataset.py --train    # eğitim setini de indir
python scripts/fetch_dataset.py --lstm     # Kaggle smoothed_errors + y_hat (kaggle.json)
```

Script test verisini, kimlik doğrulaması gerektirmeyen HuggingFace aynasından ([`appleparan/telemanom`](https://huggingface.co/datasets/appleparan/telemanom)) çeker. Telemanom deposunun README'sinde yıllarca duran doğrudan S3 adresi artık 403 döndürüyor.

`--lstm` için `pip install kaggle` ve `kaggle.json` gerekir. Anahtar `KAGGLE_CONFIG_DIR` veya `~/Downloads/.kaggle` / `~/.kaggle` altında aranır; dosya commit edilmez.

> LSTM çıktıları olmadan skor z-score + River hibritidir. Panel, veri seti yoksa `python scripts/fetch_dataset.py` uyarısı gösterir.

### 4. Backend Kurulumu
```bash
python -m venv .venv
.venv/bin/pip install -r backend/requirements.txt    # Windows: .venv\Scripts\pip.exe
```

### 5. Veritabanı migration (zorunlu)
Şema yalnızca Alembic ile güncellenir; `metadata.create_all` kullanılmaz.
```bash
cd backend && alembic upgrade head
```

### 6. Backend Sunucu
```bash
cd backend && uvicorn main:app --reload --port 8000
```
Sağlık kontrolü veri seti durumunu da gösterir:
```bash
curl http://localhost:8000/health
# {"status":"ok", "dataset":{"channels_loaded":12,"anomaly_score_source":"zscore+river","ready":true}, ...}
```

### 7. Frontend
```bash
cd frontend && npm install && npm run dev
```

### 8. Aç
Tarayıcıda [http://localhost:5173](http://localhost:5173). Geliştirmede `vite.config.js` `/api` ve `/ws` isteklerini `http://localhost:8000` adresine yönlendirir. Üretimde genelde nginx ile aynı kökenden servis edilir.

### 9. GitHub Pages (statik vitrin)

GitHub Pages yalnızca derlenmiş frontend’i yayınlar; FastAPI + Postgres orada çalışmaz. Canlı adres: [https://zehracicek.github.io/SENTINEL/](https://zehracicek.github.io/SENTINEL/)

`main`’e her push `.github/workflows/pages.yml` ile siteyi günceller. İlk seferde repo **Settings → Pages → Source: GitHub Actions** seçilmelidir.

Gösterge panelindeki canlı telemetri için ayrı bir API gerekir (`VITE_API_BASE` / `VITE_WS_URL`). NASA_ARŞİV, backend yokken NASA açık uçlarına düşer.

---

## 10. Dosya Yapısı

```
mars-rover-dashboard/
├── backend/
│   ├── main.py                 # FastAPI, lifespan: simülasyon + stats + uplink drain; CORS
│   ├── database.py             # Async engine, session, load_dotenv
│   ├── models.py               # sensor_readings, anomaly_events, transmission_log, uplink_queue
│   ├── schemas.py              # Pydantic şemalar
│   ├── crud.py                 # CRUD, istatistikler, uplink drain
│   ├── simulator.py            # MSL test .npy replay, rover durumu
│   ├── edge_processor.py     # Anomali skoru, iletim kararı, batch codec metrikleri
│   ├── compressor.py           # Delta + zlib DEFLATE
│   ├── requirements.txt
│   ├── .env.example
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/           # 001_initial_schema, 002_uplink_queue, 003_channel_ground_truth
│   ├── routers/
│   │   ├── sensor_data.py
│   │   ├── anomalies.py
│   │   ├── uplink_queue.py
│   │   ├── nasa.py             # NASA Open API proxy
│   │   └── websocket.py
│   └── data/                   # NASA SMAP/MSL veri seti (replay + smoothed_errors, .h5 mirası)
│       ├── train/
│       ├── test/
│       ├── labeled_anomalies.csv
│       └── 2018-05-19_15.00.10/
│           ├── models/         # .h5 (runtime kullanılmaz)
│           ├── y_hat/
│           ├── smoothed_errors/
│           └── params.log
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── components/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── MetricCards.jsx
│   │   │   ├── AnomalyChart.jsx
│   │   │   ├── LiveStreamTable.jsx
│   │   │   ├── BandwidthGauge.jsx
│   │   │   ├── AlertCenter.jsx
│   │   │   ├── PipelineAnimation.jsx
│   │   │   ├── SensorDetail.jsx
│   │   │   ├── RoverMap.jsx
│   │   │   ├── Telemetry.jsx
│   │   │   ├── TransmissionLog.jsx
│   │   │   ├── UplinkQueue.jsx
│   │   │   ├── DatasetInfo.jsx
│   │   │   ├── RoverThinking.jsx
│   │   │   └── ConnectionStatus.jsx
│   │   ├── hooks/
│   │   │   ├── useWebSocket.js
│   │   │   └── useAnomalyData.js
│   │   └── utils/formatters.js
│   ├── vite.config.js          # /api ve /ws → localhost:8000 proxy
│   ├── tailwind.config.js
│   └── package.json
├── scripts/
│   ├── fetch_dataset.py          # NASA MSL .npy dosyalarını indirir
│   └── score_sanity_check.py     # Skorlamayı çevrimdışı ölçer (precision/recall)
├── docker-compose.yml            # PostgreSQL (kimlik bilgileri kök .env'den)
├── .env.example                  # docker-compose kimlik bilgisi şablonu
├── deploy_sync.py                # Üretim: yerel npm build + SFTP + pip + alembic + systemd
└── README.md
```

### Üretim sunucusuna yükleme

`deploy_sync.py` yerelde `npm run build` çalıştırır; `backend` + `frontend/dist` ve kaynak aynasını SFTP ile yükler; uzakta `venv` veya Miniconda `pip` ile `requirements.txt` kurar; `alembic upgrade head` çalıştırır; systemd birimi (ör. `nirvana`) ve nginx yeniden başlatılır. Ürün arayüz adı **SENTİNEL**; sunucu dizini örneği `/opt/nirvana/` tarihsel kurulumla uyumludur. Yerel `backend/.env` varsa `/opt/nirvana/backend/.env` olarak kopyalanır ve `EnvironmentFile=-/opt/nirvana/backend/.env` systemd birimine eklenir.

Kimlik bilgileri **yalnızca ortam değişkenlerinden** okunur; repoda hiçbir sunucu adresi veya parola bulunmaz:

| Değişken | Açıklama |
|----------|----------|
| `SENTINEL_DEPLOY_HOST` | Zorunlu — sunucu adresi |
| `SENTINEL_DEPLOY_USER` | Varsayılan `root` |
| `SENTINEL_DEPLOY_KEY` | Önerilen — SSH özel anahtar dosyası |
| `SENTINEL_DEPLOY_PASSWORD` | Anahtar yoksa parola |
| `SENTINEL_DEPLOY_TRUST_NEW_HOST` | `1` ise bilinmeyen host anahtarı kabul edilir |

Host anahtarı doğrulaması varsayılan olarak **açıktır** (`RejectPolicy`). Sunucuyu ilk kez ekliyorsanız:

```bash
ssh-keyscan -H "$SENTINEL_DEPLOY_HOST" >> ~/.ssh/known_hosts
```

```powershell
$env:SENTINEL_DEPLOY_HOST="sunucu-adresiniz"
$env:SENTINEL_DEPLOY_KEY="$HOME\.ssh\id_ed25519"
python deploy_sync.py
```

> Üretimde `CORS_ALLOW_ORIGINS` ve `SENTINEL_API_TOKEN` değerlerini `/opt/nirvana/backend/.env` içinde tanımlayın. `NASA_API_KEY` NASA_ARŞİV sayfası ve `/api/nasa/*` için gerekir.

---

## 11. Referanslar

1. Hundman, K. et al. (2018). *Detecting Spacecraft Anomalies Using LSTMs and Nonparametric Dynamic Thresholding.* KDD 2018.
2. NASA SMAP/MSL Anomaly Detection Dataset — Kaggle.
3. NASA Perseverance Science Instruments — science.nasa.gov
4. Ground Processing of Data From the Mars Exploration Rovers — NASA NTRS.
5. IP in Deep Space: Key Characteristics — IETF Draft.
6. [NASA Open APIs](https://api.nasa.gov/) — APOD ve Mars Rover Photos (isteğe bağlı backend proxy: `/api/nasa/*`).
