// Sayısal skoru "Sadə / Orta / Güclü / Çox güclü" seviyesine çevirir.
// ponytail: sabit eşikler; katalog büyüyünce yüzdelik dilime geçilebilir.
const THRESHOLDS = {
  cpu_score: [12000, 22000, 34000],
  gpu_score: [3000, 9000, 16000],
  ram_gb: [12, 24, 48],
  ssd_gb: [400, 900, 1900],
};
const NAMES = ["basic", "mid", "strong", "top"];

export function levelOf(field, value) {
  const [a, b, c] = THRESHOLDS[field];
  return NAMES[value >= c ? 3 : value >= b ? 2 : value >= a ? 1 : 0];
}

export const LEVEL_TONE = {
  basic: "bg-white/[0.06] text-mist",
  mid: "bg-cyan-p/15 text-cyan-300",
  strong: "bg-indigo-p/20 text-indigo-200",
  top: "bg-purple-p/20 text-purple-200",
};

export const FIELD_LABEL = { cpu_score: "CPU", gpu_score: "GPU", ram_gb: "RAM", ssd_gb: "SSD" };
export const fmtField = (field, v) => (field.endsWith("_gb") ? `${v} GB` : Number(v).toLocaleString("tr-TR"));
