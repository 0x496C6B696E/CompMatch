import { num } from "../api.js";

/** PC bileşeninin tek satırlık, dile göre özelliği: "bal 27.000, AM5 soket, 65 W, 0,3 kq" */
export function componentSpec(t, c) {
  const bits = [];
  if (c.score) bits.push(t("spec.score", { n: num(c.score) }));
  if (c.capacity_gb) bits.push(`${c.capacity_gb} GB`);
  if (c.socket) bits.push(t("compat.socket", { socket: c.socket }));
  if (c.ram_type) bits.push(c.ram_type);
  if (c.tdp_watts) bits.push(`${c.tdp_watts} W`);
  if (c.psu_watts) bits.push(`${c.psu_watts} W PSU`);
  bits.push(t("spec.weight", { kg: Number(c.weight_kg).toLocaleString("tr-TR") }));
  return bits.join(", ");
}

/** Bileşen kategorisi -> seviye etiketi için kullanılacak gereksinim alanı ve değer. */
export function componentLevelField(c) {
  switch (c.category) {
    case "cpu": return ["cpu_score", c.score];
    case "gpu": return ["gpu_score", c.score];
    case "ram": return ["ram_gb", c.capacity_gb];
    case "ssd": return ["ssd_gb", c.capacity_gb];
    default: return null;
  }
}

/** services.build_pc'nin yapısal compat notunu cümleye çevirir. */
export function compatText(t, compat) {
  if (!compat) return null;
  if (compat.socket) return t("compat.socket", { socket: compat.socket });
  if (compat.ram_type) return compat.ram_type;
  if (compat.psu_min_w) return t("compat.psu", { w: compat.psu_min_w });
  return null;
}

/** Katalog "uygun işler" satırı: tövsiyə olunanlar önce, en fazla `max` isim, kalanı +N. */
export function fitsText(t, fits, max = 4) {
  if (!fits?.length) return t("catalog.fits.none");
  const names = fits.map((f) => (f.level === "rec" ? f.name : `${f.name} ${t("catalog.fits.min")}`));
  const shown = names.slice(0, max);
  return shown.join(", ") + (names.length > max ? ` +${names.length - max}` : "");
}
