export function formatNumber(value, decimals = 2) {
  if (value == null || isNaN(value)) return "—";
  return Number(value).toFixed(decimals);
}

export function formatBytes(bytes) {
  if (bytes === 0) return "0 B";
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(Math.abs(bytes)) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
}

export function formatTimestamp(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleTimeString("tr-TR", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function formatDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("tr-TR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function severityColor(severity) {
  const map = {
    CRITICAL: { bg: "#FF336620", text: "#FF3366", border: "#FF336640" },
    HIGH:     { bg: "#FF880020", text: "#FF8800", border: "#FF880040" },
    MEDIUM:   { bg: "#FFAA0020", text: "#FFAA00", border: "#FFAA0040" },
    LOW:      { bg: "#00F2FF20", text: "#00F2FF", border: "#00F2FF40" },
  };
  return map[severity] || { bg: "#1A1F2A", text: "#5A6580", border: "#1E2533" };
}

export function statusBadge(score) {
  const unknown = {
    label: "BİLİNMİYOR",
    bg: "#1A1F2A18",
    text: "#607080",
    border: "#2A3A4D",
  };
  if (score === undefined || score === null) return unknown;
  const n = typeof score === "number" ? score : Number(score);
  if (Number.isNaN(n)) return unknown;
  if (n >= 60) return { label: "ANOMALİ", bg: "#FF336618", text: "#FF3366", border: "#FF336640" };
  if (n >= 30) return { label: "ŞÜPHELİ", bg: "#FFAA0018", text: "#FFAA00", border: "#FFAA0040" };
  return { label: "NORMAL", bg: "#00FF8818", text: "#00FF88", border: "#00FF8840" };
}

export function sensorLabel(type) {
  const labels = {
    TEMP: "Sıcaklık",
    CH4: "Metan",
    O2: "Oksijen",
    CO2: "Karbondioksit",
    MOIST: "Nem",
    SPEC: "Spektral",
    UV: "Ultraviyole",
    PRESS: "Basınç",
  };
  return labels[type] || type;
}
