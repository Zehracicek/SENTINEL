import { useEffect, useState } from "react";
import { apiFetch } from "../utils/api";

async function loadFromNasaDirect() {
  const [apodRes, imgRes] = await Promise.allSettled([
    fetch("https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY").then((r) => {
      if (!r.ok) throw new Error(String(r.status));
      return r.json();
    }),
    fetch(
      "https://images-api.nasa.gov/search?q=curiosity%20rover%20mars&media_type=image&page_size=12"
    ).then((r) => {
      if (!r.ok) throw new Error(String(r.status));
      return r.json();
    }),
  ]);
  const photos = [];
  if (imgRes.status === "fulfilled") {
    const items = imgRes.value?.collection?.items || [];
    for (const item of items) {
      const data = (item.data || [])[0] || {};
      const href = (item.links || []).find((ln) => ln.href)?.href;
      if (!href) continue;
      photos.push({
        id: data.nasa_id || href,
        img_src: href,
        earth_date: String(data.date_created || "").slice(0, 10),
        camera: { name: (data.center || "NASA").toUpperCase() },
        title: data.title || "",
      });
    }
  }
  return {
    apod: apodRes.status === "fulfilled" ? apodRes.value : null,
    photos,
  };
}

export default function NasaArchive() {
  const [apod, setApod] = useState(null);
  const [photos, setPhotos] = useState([]);
  const [meta, setMeta] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [apodRes, photoRes] = await Promise.allSettled([
          apiFetch("/api/nasa/apod"),
          apiFetch("/api/nasa/mars-photos-recent/curiosity?limit=12"),
        ]);
        if (cancelled) return;

        let nextApod = apodRes.status === "fulfilled" ? apodRes.value : null;
        let nextPhotos = [];
        let nextMeta = null;
        if (photoRes.status === "fulfilled") {
          const body = photoRes.value;
          nextPhotos = Array.isArray(body?.photos) ? body.photos : [];
          nextMeta = body?.meta || null;
        }
        if (!nextApod || nextPhotos.length === 0) {
          const pub = await loadFromNasaDirect();
          if (cancelled) return;
          if (!nextApod) nextApod = pub.apod;
          if (nextPhotos.length === 0 && pub.photos.length) {
            nextPhotos = pub.photos;
            nextMeta = { count: pub.photos.length };
          }
        }
        if (cancelled) return;
        setApod(nextApod);
        setPhotos(nextPhotos);
        setMeta(nextMeta);
        if (!nextApod && nextPhotos.length === 0) {
          setError("NASA arşivi yanıt vermedi");
        }
      } catch (e) {
        if (!cancelled) setError(e.message || "NASA arşivi yanıt vermedi");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="space-y-5">
      <div>
        <p className="text-lg font-bold uppercase tracking-wide" style={{ color: "#BCC8D4" }}>
          NASA_AÇIK_ARŞİV
        </p>
        <p className="text-sm mt-1 max-w-3xl" style={{ color: "#708090" }}>
          Replay telemetrisi değil. NASA Open API üzerinden Günün Gökyüzü Fotoğrafı
          (APOD) ve Curiosity görselleri.
        </p>
      </div>

      {loading && (
        <div className="n-hud p-5 text-sm" style={{ color: "#708090" }}>
          NASA arşivi yükleniyor…
        </div>
      )}

      {error && !apod && photos.length === 0 && (
        <div className="n-hud p-5 space-y-2">
          <p className="text-xs font-bold uppercase tracking-widest" style={{ color: "#FFAA00" }}>
            NASA_ARŞİV_YANIT_YOK
          </p>
          <p className="text-sm" style={{ color: "#8899AA" }}>{error}</p>
        </div>
      )}

      {apod && (
        <div className="n-hud p-5 grid grid-cols-1 lg:grid-cols-2 gap-5">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest" style={{ color: "#607080" }}>
              APOD
            </p>
            <p className="text-lg font-bold mt-2" style={{ color: "#E8EEF4" }}>{apod.title}</p>
            <p className="text-xs mt-1" style={{ color: "#506070" }}>{apod.date}</p>
            <p className="text-sm mt-3 leading-relaxed" style={{ color: "#8899AA" }}>
              {apod.explanation}
            </p>
          </div>
          {apod.url && apod.media_type === "image" && (
            <img
              src={apod.url}
              alt={apod.title || "APOD"}
              className="w-full h-full max-h-80 object-cover"
              style={{ border: "1px solid #0D1520" }}
            />
          )}
        </div>
      )}

      {photos.length > 0 && (
        <div className="n-hud p-5 space-y-4">
          <div className="flex justify-between items-baseline gap-3">
            <p className="text-xs font-bold uppercase tracking-widest" style={{ color: "#607080" }}>
              CURIOSITY_GÖRSEL_ARŞİVİ
            </p>
            {meta && (
              <p className="text-xs" style={{ color: "#506070" }}>
                {meta.count} kare
              </p>
            )}
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-3">
            {photos.map((p) => (
              <a
                key={p.id}
                href={p.img_src}
                target="_blank"
                rel="noreferrer"
                className="block"
                style={{ border: "1px solid #0D1520" }}
              >
                <img src={p.img_src} alt={p.title || p.camera?.name || "NASA"} className="w-full h-36 object-cover" />
                <p className="px-2 py-1 text-[10px] uppercase tracking-wide truncate" style={{ color: "#607080" }}>
                  {p.camera?.name}
                  {p.earth_date ? ` · ${p.earth_date}` : p.sol != null ? ` · sol ${p.sol}` : ""}
                </p>
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
