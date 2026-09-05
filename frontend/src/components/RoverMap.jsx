import { useState, useEffect, useMemo, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { formatNumber } from "../utils/formatters";

/** NASA Mars Location — M20 Perseverance, Jezero (yeni sekmede; iframe CSP ile engellenir) */
export const NASA_M20_LOCATION_MAP_URL =
  "https://mars.nasa.gov/maps/location/?mission=M20&site=NOW&mapLon=77.2690773010254&mapLat=18.450463604466755&mapZoom=13&globeLon=77.23515809&globeLat=18.42769536999999&globeZoom=11&globeCamera=0,-9765.625,0,0,1,0&panePercents=0,100,0&on=Rover%20Position%241.00,Rover%20Waypoints%241.00,Rover%20Drive%20Path%241.00,Sampling%20Locations%241.00,Helicopter%20Position%241.00,Color%20Basemap%241.00,Grayscale%20Basemap%241.00,Northeast%20Syrtis%20Base%20Map%241.00";

const TRAIL_MAX = 500;
const JEZERO_CENTER = [18.4505, 77.2691];
const LANDING = [18.45046, 77.26908];
const MARS_TILES = "https://s3-eu-west-1.amazonaws.com/whereonmars.cartodb.net/viking_mdim21_global/{z}/{x}/{y}.png";

export default function RoverMap({ stats }) {
  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  const roverMarker = useRef(null);
  const trailLine = useRef(null);
  const [trail, setTrail] = useState([]);
  const lastPosKey = useRef(null);
  const [copied, setCopied] = useState(false);

  const roverLat = stats?.rover?.lat;
  const roverLon = stats?.rover?.lon;
  const sol = stats?.rover?.sol ?? "—";

  const openNASAInNewTab = () => {
    window.open(NASA_M20_LOCATION_MAP_URL, "_blank", "noopener,noreferrer");
  };

  const copyNasaLink = async () => {
    try {
      await navigator.clipboard.writeText(NASA_M20_LOCATION_MAP_URL);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* izin yok */
    }
  };

  useEffect(() => {
    if (!mapRef.current || mapInstance.current) return;

    const map = L.map(mapRef.current, {
      center: JEZERO_CENTER,
      zoom: 8,
      minZoom: 2,
      maxZoom: 9,
      zoomControl: true,
      attributionControl: false,
    });

    L.tileLayer(MARS_TILES, {
      noWrap: false,
      maxNativeZoom: 7,
      maxZoom: 9,
      tileSize: 256,
      errorTileUrl: "",
    }).addTo(map);

    L.circle(JEZERO_CENTER, {
      radius: 80000,
      color: "#FFAA0050",
      weight: 1,
      fillColor: "#FFAA0010",
      fillOpacity: 0.25,
      dashArray: "6 4",
    }).addTo(map);

    const landIcon = L.divIcon({
      className: "",
      html: `<div style="width:14px;height:14px;border-radius:50%;background:#7000FF50;border:2px solid #9060FF;box-shadow:0 0 10px #7000FF60;"></div>`,
      iconSize: [14, 14],
      iconAnchor: [7, 7],
    });

    L.marker(LANDING, { icon: landIcon })
      .addTo(map)
      .bindPopup(
        `<div style="background:#080C14;color:#BCC8D4;padding:10px;border:1px solid #1A2535;font-family:JetBrains Mono,monospace;font-size:11px;min-width:180px;">
          <p style="color:#9060FF;font-weight:bold;font-size:12px;">İNİŞ ALANI (YAKLAŞIK)</p>
          <p style="color:#708090;margin-top:6px;">M2020 Perseverance — Jezero krateri</p>
          <p style="color:#506070;margin-top:4px;">${LANDING[0].toFixed(4)}°K, ${LANDING[1].toFixed(4)}°D</p>
        </div>`,
        { className: "mars-popup" }
      );

    const roverIcon = L.divIcon({
      className: "",
      html: `<div style="position:relative;width:20px;height:20px;">
        <div style="position:absolute;inset:0;border-radius:50%;background:#00F2FF;box-shadow:0 0 14px #00F2FF,0 0 28px #00F2FF80;"></div>
        <div style="position:absolute;inset:-10px;border-radius:50%;border:1.5px solid #00F2FF40;animation:rp 2s ease-in-out infinite;"></div>
      </div>
      <style>@keyframes rp{0%,100%{transform:scale(1);opacity:1}50%{transform:scale(2);opacity:0}}</style>`,
      iconSize: [20, 20],
      iconAnchor: [10, 10],
    });

    roverMarker.current = L.marker(JEZERO_CENTER, { icon: roverIcon })
      .addTo(map)
      .bindPopup("", { className: "mars-popup" });

    trailLine.current = L.polyline([], {
      color: "#00F2FF",
      weight: 2,
      opacity: 0.4,
      dashArray: "5 5",
    }).addTo(map);

    mapInstance.current = map;
    return () => {
      map.remove();
      mapInstance.current = null;
    };
  }, []);

  useEffect(() => {
    if (roverLat == null || roverLon == null || !roverMarker.current) return;
    const key = `${roverLat},${roverLon}`;
    if (lastPosKey.current === key) return;
    lastPosKey.current = key;

    const pos = [roverLat, roverLon];
    roverMarker.current.setLatLng(pos);
    roverMarker.current.setPopupContent(
      `<div style="background:#080C14;color:#BCC8D4;padding:10px;border:1px solid #1A2535;font-family:JetBrains Mono,monospace;font-size:11px;min-width:180px;">
        <p style="color:#00F2FF;font-weight:bold;font-size:12px;">ROVER (SİM)</p>
        <p style="color:#708090;margin-top:6px;">Enlem: ${roverLat.toFixed(6)}°K</p>
        <p style="color:#708090;">Boylam: ${roverLon.toFixed(6)}°D</p>
        <p style="color:#FF00FF;margin-top:6px;font-weight:bold;">SOL: ${sol}</p>
      </div>`
    );

    setTrail((prev) => {
      const next = [...prev, pos].slice(-TRAIL_MAX);
      if (trailLine.current) trailLine.current.setLatLngs(next);
      return next;
    });
  }, [roverLat, roverLon, sol]);

  const dist = useMemo(() => {
    if (trail.length < 2) return 0;
    let d = 0;
    for (let i = 1; i < trail.length; i++) {
      const dlat = trail[i][0] - trail[i - 1][0];
      const dlon = trail[i][1] - trail[i - 1][1];
      d += Math.sqrt(dlat * dlat + dlon * dlon) * 111000;
    }
    return d;
  }, [trail]);

  const focusRover = () => {
    if (mapInstance.current && roverLat != null && roverLon != null) {
      mapInstance.current.flyTo([roverLat, roverLon], 8, { duration: 1 });
    }
  };

  const focusJezero = () => {
    if (mapInstance.current) {
      mapInstance.current.flyTo(JEZERO_CENTER, 7, { duration: 1 });
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-lg font-bold uppercase tracking-wide" style={{ color: "#BCC8D4" }}>
            ROVER HARİTASI
          </p>
          <p className="text-sm mt-1 max-w-2xl" style={{ color: "#708090" }}>
            Resmi{" "}
            <span style={{ color: "#00F2FF" }}>NASA Mars Location</span> (rover yolu, örnekleme, Ingenuity) tarayıcı
            güvenliği nedeniyle yalnızca <span style={{ color: "#BCC8D4" }}>yeni sekmede</span> açılabilir; aşağıda panel
            telemetrisi için yerel Mars haritası gösterilir.
          </p>
        </div>
        <div className="flex flex-wrap gap-2 shrink-0">
          <button type="button" onClick={openNASAInNewTab} className="n-btn-primary text-xs py-2 px-4">
            NASA SİTESİNDE AÇ
          </button>
          <button
            type="button"
            onClick={copyNasaLink}
            className="n-btn-primary text-xs py-2 px-4"
            style={{ borderColor: "#FFAA0040", color: "#FFAA00", background: "#FFAA0010" }}
          >
            {copied ? "KOPYALANDI" : "BAĞLANTIYI KOPYALA"}
          </button>
        </div>
      </div>

      <div
        className="n-hud px-4 py-3 text-xs sm:text-sm leading-relaxed"
        style={{ background: "#080C14", border: "1px solid #0D1520", color: "#607080" }}
      >
        <span style={{ color: "#FFAA00" }}>Neden iframe yok? </span>
        NASA, <code style={{ color: "#506070" }}>Content-Security-Policy: frame-ancestors</code> ile haritayı yalnızca{" "}
        <span style={{ color: "#8899AA" }}>nasa.gov</span> üzerinden çerçevelemeye izin veriyor; bu kural sunucu
        tarafında tanımlıdır ve üçüncü taraf sitelerde (ör. bu panel) <span style={{ color: "#BCC8D4" }}>kodla
        kaldırılamaz</span>. Çözüm: resmi aracı yeni sekmede kullanmak veya aşağıdaki yerel haritayı kullanmak.
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-5">
        <div
          className="xl:col-span-3 relative n-hud overflow-hidden flex flex-col gap-3"
          style={{ height: "calc(100vh - 230px)", minHeight: "480px" }}
        >
          <div className="flex flex-wrap gap-2 shrink-0">
            <button type="button" onClick={focusRover} className="n-btn-primary text-xs py-2 px-4">
              ROVER&apos;A ODAKLAN
            </button>
            <button
              type="button"
              onClick={focusJezero}
              className="n-btn-primary text-xs py-2 px-4"
              style={{ borderColor: "#FFAA0040", color: "#FFAA00", background: "#FFAA0010" }}
            >
              JEZERO MERKEZİ
            </button>
          </div>

          <div className="relative flex-1 min-h-[320px] overflow-hidden rounded border" style={{ borderColor: "#0D1520" }}>
            <div ref={mapRef} className="w-full h-full min-h-[320px]" />

            <div className="absolute top-3 left-14 z-[1000] pointer-events-none max-w-[min(100%,20rem)]">
              <div className="p-3 pointer-events-auto" style={{ background: "#060910E0", border: "1px solid #0D1520" }}>
                <p className="text-xs font-bold uppercase tracking-widest" style={{ color: "#00F2FF" }}>
                  YEREL ÖNİZLEME
                </p>
                <p className="text-xs mt-0.5" style={{ color: "#506070" }}>
                  Viking MDIM21 — simülasyon konumu
                </p>
              </div>
            </div>

            <div className="absolute top-3 right-3 z-[1000] pointer-events-none">
              <div
                className="p-3 space-y-1 pointer-events-auto"
                style={{ background: "#060910E0", border: "1px solid #0D1520", minWidth: "170px" }}
              >
                {[
                  { l: "ENLEM", v: roverLat != null ? `${formatNumber(roverLat, 4)}°K` : "—", c: "#00F2FF" },
                  { l: "BOYLAM", v: roverLon != null ? `${formatNumber(roverLon, 4)}°D` : "—", c: "#00F2FF" },
                  { l: "SOL", v: sol, c: "#FF00FF" },
                  { l: "MESAFE", v: `${formatNumber(dist, 1)} m`, c: "#00FF88" },
                ].map((m) => (
                  <div key={m.l} className="flex justify-between gap-2">
                    <span className="text-xs font-bold uppercase shrink-0" style={{ color: "#506070" }}>
                      {m.l}
                    </span>
                    <span className="text-xs font-bold text-right truncate" style={{ color: m.c }} title={String(m.v)}>
                      {m.v}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="n-hud p-5">
            <p className="text-xs font-bold uppercase tracking-widest mb-3" style={{ color: "#607080" }}>
              RESMİ NASA HARİTASI
            </p>
            <div className="space-y-2 text-sm" style={{ color: "#708090" }}>
              <p>
                Tüm görev katmanları için <span style={{ color: "#00F2FF" }}>NASA sitesinde aç</span> düğmesini
                kullanın — aynı bağlantı, tarayıcıda tam özellikli çalışır.
              </p>
            </div>
          </div>

          <div className="n-hud p-5">
            <p className="text-xs font-bold uppercase tracking-widest mb-3" style={{ color: "#607080" }}>
              YEREL HARİTA
            </p>
            <div className="space-y-2 text-sm" style={{ color: "#708090" }}>
              <p>
                <span style={{ color: "#00F2FF" }}>Tekerlek / sürükle</span> — Yakınlaştır ve kaydır
              </p>
              <p>
                <span style={{ color: "#00F2FF" }}>Tıkla</span> — İşaretçi bilgisi
              </p>
            </div>
          </div>

          <div className="n-hud p-5">
            <p className="text-xs font-bold uppercase tracking-widest mb-3" style={{ color: "#607080" }}>
              PANEL TELEMETRİSİ (SIM)
            </p>
            <div className="space-y-2">
              {[
                { l: "ENLEM", v: roverLat != null ? `${formatNumber(roverLat, 6)}°K` : "—", c: "#00F2FF" },
                { l: "BOYLAM", v: roverLon != null ? `${formatNumber(roverLon, 6)}°D` : "—", c: "#00F2FF" },
                { l: "SOL (MARS GÜNÜ)", v: sol, c: "#FF00FF" },
                { l: "İZ NOKTASI", v: trail.length, c: "#8899AA" },
                { l: "TOPLAM MESAFE", v: `${formatNumber(dist, 1)} m`, c: "#00FF88" },
              ].map((m) => (
                <div
                  key={m.l}
                  className="flex items-center justify-between px-3 py-2"
                  style={{ background: "#050810", border: "1px solid #0D1520" }}
                >
                  <span className="text-xs font-bold uppercase tracking-wide" style={{ color: "#506070" }}>
                    {m.l}
                  </span>
                  <span className="text-sm font-bold" style={{ color: m.c }}>
                    {m.v}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="n-hud p-5">
            <p className="text-xs font-bold uppercase tracking-widest mb-3" style={{ color: "#607080" }}>
              JEZERO (M2020)
            </p>
            <div className="space-y-2 text-sm leading-relaxed" style={{ color: "#708090" }}>
              <p>
                Yerel harita Jezero çevresini gösterir; NASA aracı güncel rover yolu ve helikopteri içerir.
              </p>
            </div>
          </div>

          <div className="n-hud p-5">
            <p className="text-xs font-bold uppercase tracking-widest mb-3" style={{ color: "#607080" }}>
              KAYNAK
            </p>
            <div className="space-y-1.5 text-xs" style={{ color: "#607080" }}>
              <a
                href={NASA_M20_LOCATION_MAP_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="break-all underline hover:no-underline"
                style={{ color: "#00F2FF" }}
              >
                mars.nasa.gov/maps/location (M20)
              </a>
              <p>NASA / JPL</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
