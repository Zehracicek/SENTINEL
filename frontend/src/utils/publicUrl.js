/** Vite `base` (GitHub Pages: /SENTINEL/) altındaki statik dosya yolu. */
export function publicUrl(path) {
  const base = import.meta.env.BASE_URL || "/";
  const clean = String(path || "").replace(/^\//, "");
  return `${base}${clean}`;
}

export const ROVER_GLB_URL = publicUrl("models/perseverance.glb");
