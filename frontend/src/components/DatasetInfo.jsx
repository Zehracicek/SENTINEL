import EvaluationMetrics from "./EvaluationMetrics";

const PAPER_PARAMS = [
  { key: "KATMANLAR", val: "2 × LSTM (80 birim)" },
  { key: "BATCH_SIZE", val: "70" },
  { key: "EPOCHS", val: "35" },
  { key: "DROPOUT", val: "0.3" },
  { key: "OPTIMİZER", val: "Adam" },
  { key: "LOSS", val: "MSE" },
  { key: "SEQUENCE_LENGTH", val: "250 timestep" },
  { key: "WINDOW_SIZE", val: "30" },
];

const CHANNELS = [
  { id: "T-1", type: "TEMP", craft: "MSL", desc: "Sıcaklık sensörü", shape: "8612×25" },
  { id: "T-2", type: "TEMP", craft: "MSL", desc: "Termal kontrol", shape: "8625×25" },
  { id: "P-10", type: "PRESS", craft: "MSL", desc: "Basınç sistemi", shape: "6100×55" },
  { id: "P-14", type: "PRESS", craft: "MSL", desc: "Hidrolik basınç", shape: "6100×55" },
  { id: "M-6", type: "CH4", craft: "MSL", desc: "Metan dedektörü", shape: "2049×55" },
  { id: "M-7", type: "MOIST", craft: "MSL", desc: "Nem sensörü", shape: "2156×55" },
  { id: "C-1", type: "SPEC", craft: "MSL", desc: "Spektrometre A", shape: "2264×55" },
  { id: "C-2", type: "SPEC", craft: "MSL", desc: "Spektrometre B", shape: "2051×55" },
  { id: "D-14", type: "UV", craft: "MSL", desc: "UV radyasyon", shape: "2625×55" },
  { id: "D-15", type: "O2", craft: "MSL", desc: "Oksijen sensörü", shape: "2158×55" },
  { id: "D-16", type: "CO2", craft: "MSL", desc: "CO₂ sensörü", shape: "2191×55" },
  { id: "F-7", type: "SPEC", craft: "MSL", desc: "FTIR spektroskopi", shape: "5054×55" },
];

function StatCard({ label, value, sub, color }) {
  return (
    <div className="n-hud p-5" style={{ background: "linear-gradient(135deg, #080C14, #060910)" }}>
      <p className="text-xs font-bold uppercase tracking-widest" style={{ color: "#607080" }}>{label}</p>
      <p className="text-3xl font-extrabold mt-2" style={{ color, textShadow: `0 0 12px ${color}40` }}>{value}</p>
      {sub && <p className="text-xs mt-1" style={{ color: "#506070" }}>{sub}</p>}
    </div>
  );
}

export default function DatasetInfo() {
  return (
    <div className="space-y-5">
      <div>
        <p className="text-lg font-bold uppercase tracking-wide" style={{ color: "#BCC8D4" }}>VERİ_SETİ_BİLGİSİ</p>
        <p className="text-sm mt-1" style={{ color: "#708090" }}>
          NASA SMAP/MSL — Hundman et al., KDD 2018. Bu panel 12 MSL kanalını replay eder; aşağıdaki canlı metrikler
          <span style={{ color: "#BCC8D4" }}> bu edge işlemcisinin</span> skorudur, makalenin değil.
        </p>
      </div>

      <EvaluationMetrics />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="BU_SİMÜLASYON" value="12" sub="MSL kanalı replay" color="#00F2FF" />
        <StatCard label="TAM_VERİ_SETİ" value="82" sub="54 SMAP + 28 MSL (makale)" color="#FF00FF" />
        <StatCard label="ANOMALİ_SEKANS" value="105" sub="Tüm 82 kanalda etiketlenmiş" color="#FF3366" />
        <StatCard label="TELEMETRİ" value="[-1, 1]" sub="Test min/max ile normalize" color="#FFAA00" />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        <div className="n-hud p-5">
          <p className="text-xs font-bold uppercase tracking-widest mb-2" style={{ color: "#607080" }}>
            MAKALE_LSTM_PARAMETRELERİ
          </p>
          <p className="text-xs mb-4 leading-relaxed" style={{ color: "#506070" }}>
            Hundman et al. boru hattı. Bu repoda Keras çalıştırılmaz; `smoothed_errors/*.npy` varsa ham hata
            sinyali okunur, yoksa z-score + River kullanılır.
          </p>
          <div className="space-y-1">
            {PAPER_PARAMS.map((p) => (
              <div key={p.key} className="flex items-center justify-between px-3 py-2" style={{ background: "#050810", border: "1px solid #0D1520" }}>
                <span className="text-xs font-bold uppercase tracking-wide" style={{ color: "#708090" }}>{p.key}</span>
                <span className="text-sm font-bold" style={{ color: "#BCC8D4" }}>{p.val}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-5">
          <div className="n-hud p-5">
            <p className="text-xs font-bold uppercase tracking-widest mb-2" style={{ color: "#607080" }}>
              REFERANS_MAKALE_SKORU
            </p>
            <p className="text-xs mb-4 leading-relaxed" style={{ color: "#506070" }}>
              LSTM + nonparametrik dinamik eşik — 82 kanal, KDD 2018. Bu sistemin canlı F1 değerinin yanına
              konmamalıdır.
            </p>
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-4" style={{ background: "#050810", border: "1px solid #0D1520" }}>
                <p className="text-xs font-bold uppercase tracking-widest" style={{ color: "#607080" }}>PRECISION</p>
                <p className="text-4xl font-extrabold mt-2" style={{ color: "#8899AA" }}>%87.5</p>
                <p className="text-xs mt-1" style={{ color: "#506070" }}>SMAP+MSL toplam</p>
              </div>
              <div className="text-center p-4" style={{ background: "#050810", border: "1px solid #0D1520" }}>
                <p className="text-xs font-bold uppercase tracking-widest" style={{ color: "#607080" }}>RECALL</p>
                <p className="text-4xl font-extrabold mt-2" style={{ color: "#8899AA" }}>%80.0</p>
                <p className="text-xs mt-1" style={{ color: "#506070" }}>F0.5 = 0.71</p>
              </div>
            </div>
          </div>

          <div className="n-hud p-5">
            <p className="text-xs font-bold uppercase tracking-widest mb-3" style={{ color: "#607080" }}>
              BU_SİSTEMİN_SKOR_YOLU
            </p>
            <div className="space-y-2 text-sm" style={{ color: "#8899AA" }}>
              <p><span style={{ color: "#00F2FF" }}>1.</span> `smoothed_errors` varsa: skor = 0.50 × LSTM + 0.50 × River</p>
              <p><span style={{ color: "#00F2FF" }}>2.</span> Yoksa: skor = 0.40 × z-score + 0.60 × River (yüzdelik kalibre)</p>
              <p><span style={{ color: "#00F2FF" }}>3.</span> Tek eşik (40–85): batarya + RL; `is_anomaly` = `uplink_eligible`</p>
              <p><span style={{ color: "#00F2FF" }}>4.</span> Etiket (`ground_truth_anomaly`) karara girmez; yalnızca değerlendirme içindir</p>
            </div>
          </div>
        </div>
      </div>

      <div className="n-hud p-5">
        <p className="text-xs font-bold uppercase tracking-widest mb-2" style={{ color: "#607080" }}>
          KULLANILAN_MSL_KANALLARI
        </p>
        <p className="text-xs mb-4" style={{ color: "#506070" }}>
          Boyutlar `backend/data/test/*.npy` dosyalarından. İlk sütun telemetri; kalanı komut one-hot (simülatör okumaz).
        </p>
        <div style={{ background: "#050810", border: "1px solid #0D1520" }} className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr style={{ borderBottom: "1px solid #0F1923" }}>
                {["KANAL_ID", "SENSÖR_TİPİ", "UZAY_ARACI", "AÇIKLAMA", "TEST_BOYUTU"].map((h) => (
                  <th key={h} className="py-3 px-4 text-xs font-bold uppercase tracking-wider text-left" style={{ color: "#607080" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {CHANNELS.map((ch) => (
                <tr key={ch.id} style={{ borderBottom: "1px solid #0A0F18" }}>
                  <td className="py-2.5 px-4 text-sm font-bold" style={{ color: "#00F2FF" }}>{ch.id}</td>
                  <td className="py-2.5 px-4 text-sm font-bold" style={{ color: "#BCC8D4" }}>{ch.type}</td>
                  <td className="py-2.5 px-4 text-sm" style={{ color: "#708090" }}>{ch.craft}</td>
                  <td className="py-2.5 px-4 text-sm" style={{ color: "#8899AA" }}>{ch.desc}</td>
                  <td className="py-2.5 px-4 text-sm font-mono" style={{ color: "#607080" }}>{ch.shape}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="n-hud p-5">
        <p className="text-xs font-bold uppercase tracking-widest mb-3" style={{ color: "#607080" }}>REFERANSLAR</p>
        <div className="space-y-2 text-sm" style={{ color: "#708090" }}>
          <p>Hundman, K. et al. (2018). <span style={{ color: "#BCC8D4" }}>&quot;Detecting Spacecraft Anomalies Using LSTMs and Nonparametric Dynamic Thresholding&quot;</span> — KDD 2018</p>
          <p>Veri: <span style={{ color: "#00F2FF" }}>khundman/telemanom</span> · ayna: HuggingFace appleparan/telemanom · tam paket: Kaggle</p>
        </div>
      </div>
    </div>
  );
}
