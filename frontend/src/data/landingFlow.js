/** Ana sayfa: veri akışı (panel VERİ_AKIŞI ile aynı sıra) */

export const LANDING_FLOW_STEPS = [
  {
    id: "collect",
    title: "Veri toplama",
    subtitle: "Sensör okuma",
    short: "MSL tabanlı 12 kanal; normalize telemetri ve zaman damgası.",
    detail:
      "NASA SMAP/MSL veri setinden 12 MSL kanalı okunur. Değerler [-1, 1] aralığında; CCSDS benzeri paket yapısı ile edge simülatörüne akar.",
    color: "#00F2FF",
    panelPath: "/telemetri",
    panelLabel: "Telemetri paneli",
  },
  {
    id: "buffer",
    title: "Tamponlama",
    subtitle: "Uç tamponu (SSR)",
    short: "Ring buffer ile son okumalar; kritik skorlar öncelikli sıraya alınır.",
    detail:
      "Sensör tipi başına dairesel tampon (ör. 500 okuma). Yüksek anomali skoru anında sonraki aşamaya; düşük öncelik sıraya kalır.",
    color: "#9060FF",
    panelPath: "/veri_akisi",
    panelLabel: "Veri akışı animasyonu",
  },
  {
    id: "anomaly",
    title: "Anomali tespiti",
    subtitle: "z-score + River (LSTM opsiyonel)",
    short: "smoothed_errors varsa LSTM hatası, yoksa z-score; ikisi de River ile harmanlanır.",
    detail:
      "Keras çalışma anında yüklenmez. Dosya varsa skor = 0.50×LSTM + 0.50×River; yoksa 0.40×z-score + 0.60×River (yüzdelik kalibre). Canlı metrik VERİ_SETİ sayfasındadır.",
    color: "#FFAA00",
    panelPath: "/anomali_tespit",
    panelLabel: "Anomali merkezi",
  },
  {
    id: "decision",
    title: "Karar motoru",
    subtitle: "Tek dinamik eşik",
    short: "skor ≥ eşik ise ilet; aksi halde düşür. Eşik 40–85 (batarya + RL).",
    detail:
      "Üç bant yoktur. is_anomaly ve uplink_eligible aynı koşuldur. Taban eşik bataryaya göre 50/60/70; RL ±5 ekler.",
    color: "#FF3366",
    panelPath: "/uplink_kuyrugu",
    panelLabel: "Uplink kuyruğu",
  },
  {
    id: "priority",
    title: "Önceliklendirme",
    subtitle: "Bilimsel sınıf",
    short: "Anomali tipine göre öncelik; çoklu sensör uyumu yüksek önem derecesi verir.",
    detail:
      "Organik imza, metan artışı, spektral sapma vb. tipler bilimsel öncelik skoruna (ör. /10) dönüştürülür.",
    color: "#FF00FF",
    panelPath: "/anomali_tespit",
    panelLabel: "Alarm listesi",
  },
  {
    id: "compress",
    title: "Sıkıştırma",
    subtitle: "Delta + DEFLATE",
    short: "Seçilmiş paketler delta kodlanır ve zlib ile sıkıştırılır.",
    detail:
      "float64 çiftleri delta + zlib seviye 6; stats_update ile sıkıştırma oranı ve tasarruf yüzdesi canlı izlenir.",
    color: "#00FF88",
    panelPath: "/iletim_analizi",
    panelLabel: "İletim analizi",
  },
  {
    id: "transmit",
    title: "DSN iletimi",
    subtitle: "Derin uzay ağı",
    short: "Gecikmeli bağlantı modeli; store-and-forward ile güvenli iletim.",
    detail:
      "Tek yön ışık gecikmesi dakikalar mertebesinde; simülasyonda periyodik drain ile paketler iletilmiş sayılır.",
    color: "#00B8D4",
    panelPath: "/iletim_analizi",
    panelLabel: "DSN özeti",
  },
  {
    id: "ground",
    title: "Yer istasyonu",
    subtitle: "Birleştirme & panel",
    short: "PostgreSQL, REST ve WebSocket ile canlı operasyon paneli.",
    detail:
      "Okumalar ve anomaliler veritabanında; WebSocket ile gösterge paneline düşük gecikmeli yayın.",
    color: "#8899AA",
    panelPath: "/gosterge_paneli",
    panelLabel: "Gösterge paneli",
  },
];

export const LANDING_AI_BLOCK = {
  title: "Yapay zekâ analiz ve eğitim",
  subtitle: "Anomali (03) ile karar motoru (04) arasında: sürekli öğrenme ve öneri",
  items: [
    {
      head: "LSTM sinyali (opsiyonel)",
      text: "Yalnızca Kaggle smoothed_errors varsa; aksi halde z-score + River.",
      icon: "activity",
    },
    {
      head: "River (çevrimiçi)",
      text: "HalfSpaceTrees ile akış üzerinde anlık model güncellemesi.",
      icon: "git-branch",
    },
    {
      head: "Pekiştirmeli öğrenme",
      text: "Uplink geri bildirimi ile Q-tablo ve eşik ince ayarı.",
      icon: "zap",
    },
    {
      head: "Yer bulutu önerisi",
      text: "Simüle eşik önerisi ve sürüm sayacı — federated learning değil.",
      icon: "cloud-cog",
    },
    {
      head: "Rover düşünce",
      text: "Groq ile isteğe bağlı açıklama; panelden aç/kapa.",
      icon: "sparkles",
    },
  ],
};

export function getFlowNodePositions(count = 8) {
  const positions = [];
  for (let i = 0; i < count; i++) {
    const t = count === 1 ? 0.5 : i / (count - 1);
    const x = -5.2 + t * 10.4;
    const z = Math.sin(t * Math.PI) * 0.65;
    const y = Math.sin(t * Math.PI * 1.6) * 0.12;
    positions.push([x, y, z]);
  }
  return positions;
}

export function getAiNodePosition(positions) {
  if (positions.length < 4) return [0, 0.85, 0.5];
  const a = positions[2];
  const b = positions[3];
  return [(a[0] + b[0]) / 2, 0.95, (a[2] + b[2]) / 2 + 0.85];
}
