import { useLang } from "../i18n/index.jsx";
import { fmtField } from "../lib/levels.js";
import { LevelPill } from "./SpecChips.jsx";

export const FIELDS = ["cpu_score", "gpu_score", "ram_gb", "ssd_gb"];

/** Seçili programların alan bazında en yüksek min/önerilen değerleri (backend ile aynı kural). */
export function ceiling(selected) {
  const agg = { min: {}, rec: {} };
  for (const key of FIELDS) {
    agg.min[key] = Math.max(0, ...selected.map((p) => p[`min_${key}`]));
    agg.rec[key] = Math.max(0, ...selected.map((p) => p[`rec_${key}`]));
  }
  return agg;
}

function Bar({ field, min, rec, scale, selected }) {
  const { t } = useLang();
  const pct = (v) => `${Math.min(100, (v / scale) * 100)}%`;
  const setter = selected.find((p) => p[`rec_${field}`] === rec);
  return (
    <div>
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-0.5 text-sm">
        <span className="flex shrink-0 items-center gap-2 whitespace-nowrap text-snow">
          {t(`field.${field}`)} <LevelPill field={field} value={rec} />
        </span>
        <span className="num ml-auto whitespace-nowrap text-mist">
          {t("req.min")} <span className="text-cyan-200">{fmtField(field, min)}</span>
          <span className="mx-2 text-white/15">/</span>
          {t("req.rec")} <span className="font-semibold text-snow">{fmtField(field, rec)}</span>
        </span>
      </div>
      <div className="relative mt-2 h-2.5 rounded-md bg-white/[0.06]">
        <div className="bar-grow absolute inset-y-0 left-0 rounded-md bg-indigo-p shadow-[0_0_12px_rgba(99,102,241,0.45)]" style={{ width: pct(rec) }} />
        <div className="bar-grow absolute inset-y-0 left-0 rounded-md bg-cyan-p/70" style={{ width: pct(min) }} />
        {selected.map((p) => (
          <span
            key={p.id}
            title={`${p.name}: ${fmtField(field, p[`rec_${field}`])}`}
            className="absolute -top-1 h-[calc(100%+8px)] w-px bg-white/70"
            style={{ left: pct(p[`rec_${field}`]) }}
          />
        ))}
      </div>
      <p className="mt-1.5 min-h-4 text-xs text-mist">
        {setter && selected.length > 1 ? t("req.setter", { program: setter.name }) : ""}
      </p>
    </div>
  );
}

/**
 * Dört benchmark çubuğu. Turkuaz: minimum, indigo: önerilen, beyaz tikler: seçili her programın önerilen değeri.
 * `requirements` verilirse (sunucu sonucu) o kullanılır; yoksa seçili programlardan canlı hesaplanır.
 */
export default function RequirementBars({ programs, selected, requirements, hint }) {
  const { t } = useLang();
  const req = requirements ?? ceiling(selected);
  return (
    <section className="glass rounded-2xl p-5 sm:p-6">
      <h2 className="font-display text-2xl font-semibold leading-tight text-snow">{t("req.title")}</h2>
      <p className="mt-1 max-w-[60ch] text-sm text-mist">{hint}</p>
      {selected.length === 0 ? (
        <p className="mt-6 text-sm text-mist">{t("req.empty")}</p>
      ) : (
        <div className="mt-6 space-y-5">
          {FIELDS.map((f) => (
            <Bar
              key={f}
              field={f}
              min={req.min[f]}
              rec={req.rec[f]}
              scale={Math.max(req.rec[f], ...programs.map((p) => p[`rec_${f}`]), 1)}
              selected={selected}
            />
          ))}
          <p className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-mist">
            <span className="inline-flex items-center gap-1.5"><i className="inline-block h-2 w-3 rounded-sm bg-cyan-p/70" /> {t("req.min")}</span>
            <span className="inline-flex items-center gap-1.5"><i className="inline-block h-2 w-3 rounded-sm bg-indigo-p" /> {t("req.rec")}</span>
            <span className="inline-flex items-center gap-1.5"><i className="inline-block h-3 w-px bg-white/70" /> {t("req.legend.tick")}</span>
          </p>
        </div>
      )}
    </section>
  );
}
