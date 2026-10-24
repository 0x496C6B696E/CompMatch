import { num } from "../api.js";
import { useLang } from "../i18n/index.jsx";
import { LEVEL_TONE, levelOf } from "../lib/levels.js";

/** "Güclü" gibi seviye etiketi: sayıyı bilmeyen de anlasın. */
export function LevelPill({ field, value }) {
  const { t } = useLang();
  const lvl = levelOf(field, value);
  return <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${LEVEL_TONE[lvl]}`}>{t(`level.${lvl}`)}</span>;
}

/** Laptop için 4 özellik kutusu: ad, seviye etiketi, skor. */
export default function SpecChips({ laptop }) {
  const { t } = useLang();
  const items = [
    { label: t("spec.cpu"), value: laptop.cpu, field: "cpu_score", n: laptop.cpu_score, sub: t("spec.score", { n: num(laptop.cpu_score) }) },
    { label: t("spec.gpu"), value: laptop.gpu, field: "gpu_score", n: laptop.gpu_score, sub: t("spec.score", { n: num(laptop.gpu_score) }) },
    { label: t("spec.ram"), value: `${laptop.ram_gb} GB`, field: "ram_gb", n: laptop.ram_gb },
    { label: t("spec.ssd"), value: `${laptop.ssd_gb} GB`, field: "ssd_gb", n: laptop.ssd_gb },
  ];
  return (
    <div className="grid grid-cols-2 gap-2 lg:grid-cols-4">
      {items.map((s) => (
        <div key={s.field} className="rounded-xl bg-white/[0.03] px-3 py-2">
          <div className="flex items-center justify-between gap-2 text-xs text-mist">
            <span>{s.label}</span>
            <LevelPill field={s.field} value={s.n} />
          </div>
          <div className="mt-1 text-sm leading-snug text-snow">{s.value}</div>
          {s.sub && <div className="num text-xs text-mist">{s.sub}</div>}
        </div>
      ))}
    </div>
  );
}
