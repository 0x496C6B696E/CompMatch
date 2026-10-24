import { azn } from "../api.js";
import { useLang } from "../i18n/index.jsx";
import { compatText, componentLevelField, componentSpec } from "../lib/spec.js";
import PriceCompare from "./PriceCompare.jsx";
import { LevelPill } from "./SpecChips.jsx";

const MEETS_TONE = {
  rec: "bg-green-p/15 text-green-p",
  min: "bg-cyan-p/15 text-cyan-300",
  below: "bg-rose-500/15 text-rose-300",
};

export default function PcResults({ components, settings }) {
  const { t } = useLang();
  const found = components.filter((p) => p.component);
  const allLocal = found.reduce((s, p) => s + Number(p.prices?.local?.find((o) => o.in_stock)?.price_azn ?? p.prices?.best?.total_azn ?? 0), 0);
  const bestMix = found.reduce((s, p) => s + Number(p.prices?.best?.total_azn ?? 0), 0);
  const saving = allLocal - bestMix;
  const max = Math.max(allLocal, bestMix, 1);

  return (
    <div className="space-y-6">
      <section className="glass rounded-2xl p-5 sm:p-6">
        <h3 className="font-display text-2xl font-semibold leading-tight text-snow">{t("pc.total.title")}</h3>
        <p className="mt-1 max-w-[60ch] text-sm text-mist">
          {saving > 0 ? t("pc.total.saving", { amount: azn(saving) }) : t("pc.total.localOnly")}
        </p>
        <ul className="mt-5 space-y-3">
          {[
            [t("pc.total.allLocal"), allLocal, "bg-cyan-p"],
            [t("pc.total.best"), bestMix, "bg-green-p shadow-[0_0_12px_rgba(16,185,129,0.45)]"],
          ].map(([label, value, cls]) => (
            <li key={label} className="flex items-center gap-3 text-sm">
              <span className="w-32 shrink-0 text-mist sm:w-56">{label}</span>
              <div className="h-3 flex-1 rounded-sm bg-white/[0.05]">
                <div className={`bar-grow h-full rounded-sm ${cls}`} style={{ width: `${(value / max) * 100}%` }} />
              </div>
              <span className="num w-24 shrink-0 text-right font-display text-lg font-semibold text-snow">{azn(value)}</span>
            </li>
          ))}
        </ul>
      </section>

      <ol className="space-y-6">
        {components.map(({ category, component, meets, compat, prices }) => {
          const lvl = component ? componentLevelField(component) : null;
          const note = compatText(t, compat);
          return (
            <li key={category} className="glass rounded-2xl p-5 sm:p-6">
              <header className="flex flex-wrap items-start justify-between gap-x-6 gap-y-3">
                <div className="min-w-0">
                  <p className="text-sm text-mist">{t(`cat.${category}`)}</p>
                  {component ? (
                    <>
                      <h3 className="font-display text-2xl font-semibold leading-tight text-snow">{component.name}</h3>
                      <p className="num mt-1 text-sm text-mist">{component.brand}, {componentSpec(t, component)}</p>
                    </>
                  ) : (
                    <>
                      <h3 className="font-display text-2xl font-semibold leading-tight text-rose-300">{t("pc.notFound")}</h3>
                      <p className="mt-1 text-sm text-mist">{t("pc.notFound.hint", { compat: note ?? "" })}</p>
                    </>
                  )}
                  <p className="mt-2 max-w-[60ch] text-xs text-mist">{t(`cat.${category}.explain`)}</p>
                </div>
                {component && (
                  <div className="flex shrink-0 flex-wrap gap-2 text-xs">
                    {lvl && <LevelPill field={lvl[0]} value={lvl[1]} />}
                    <span className={`rounded-full px-3 py-1 font-medium ${MEETS_TONE[meets]}`}>{t(`meets.${meets}`)}</span>
                    {note && <span className="rounded-full bg-purple-p/15 px-3 py-1 text-purple-300">{note}</span>}
                  </div>
                )}
              </header>
              {component && (
                <div className="mt-6">
                  <PriceCompare prices={prices} settings={settings} />
                </div>
              )}
            </li>
          );
        })}
      </ol>
    </div>
  );
}
