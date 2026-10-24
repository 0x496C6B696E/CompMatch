import { azn } from "../api.js";
import { useLang } from "../i18n/index.jsx";
import PriceCompare from "./PriceCompare.jsx";
import SpecChips from "./SpecChips.jsx";

const TIER_TONE = { value: "text-cyan-300", recommended: "text-indigo-300", pro: "text-purple-300" };

export default function LaptopResults({ laptops, settings }) {
  const { t } = useLang();
  if (!laptops?.length) {
    return <p className="glass rounded-2xl p-6 text-mist">{t("laptops.empty")}</p>;
  }
  return (
    <ol className="space-y-6">
      {laptops.map(({ tier, laptop, meets, prices }, i) => {
        const best = prices?.best;
        const summary = best
          ? t("summary.laptop", { name: laptop.name, fit: t(`summary.fit.${meets}`), store: best.store, price: azn(best.total_azn) })
          : t("summary.noPrice", { name: laptop.name, fit: t(`summary.fit.${meets}`) });
        return (
          <li key={laptop.id} className="glass rounded-2xl p-5 sm:p-6">
            <header className="flex flex-wrap items-start justify-between gap-x-6 gap-y-3">
              <div className="min-w-0">
                <p className={`text-sm font-medium ${TIER_TONE[tier]}`}>
                  {i + 1}. {t(`tier.${tier}`)}
                </p>
                <h3 className="font-display text-2xl font-semibold leading-tight text-snow sm:text-3xl">{laptop.name}</h3>
                <p className="mt-1 text-sm text-mist">
                  {laptop.brand}, {laptop.screen}, {t("spec.weight", { kg: Number(laptop.weight_kg).toLocaleString("tr-TR") })}
                </p>
              </div>
              <span className={`shrink-0 rounded-full px-3 py-1 text-xs font-medium ${meets === "rec" ? "bg-green-p/15 text-green-p" : "bg-cyan-p/15 text-cyan-300"}`}>
                {t(`meets.${meets}`)}
              </span>
            </header>

            <p className="mt-4 rounded-xl border border-indigo-p/30 bg-indigo-p/10 px-4 py-3 text-sm leading-relaxed text-snow">{summary}</p>

            <div className="mt-4">
              <SpecChips laptop={laptop} />
            </div>

            <div className="mt-6">
              <PriceCompare prices={prices} settings={settings} />
            </div>
          </li>
        );
      })}
    </ol>
  );
}
