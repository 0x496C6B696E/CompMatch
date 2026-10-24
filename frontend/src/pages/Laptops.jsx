import { useEffect, useMemo, useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { azn, getLaptops, getSettings } from "../api.js";
import { useLang } from "../i18n/index.jsx";
import { fitsText } from "../lib/spec.js";
import Explain from "../components/Explain.jsx";
import PriceCompare, { CostLegend } from "../components/PriceCompare.jsx";
import SpecChips from "../components/SpecChips.jsx";
import { Heading, btnGhost } from "./Wizard.jsx";

export function Chip({ active, onClick, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={`shrink-0 rounded-full px-3.5 py-1.5 text-sm transition-colors ${
        active ? "bg-indigo-p text-white" : "glass text-mist hover:text-snow"
      }`}
    >
      {children}
    </button>
  );
}

export function SortSelect({ value, onChange }) {
  const { t } = useLang();
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="glass rounded-full bg-transparent px-3.5 py-1.5 text-sm text-snow"
    >
      <option value="price" className="bg-surface">{t("catalog.sort.price")}</option>
      <option value="perf" className="bg-surface">{t("catalog.sort.perf")}</option>
    </select>
  );
}

const cost = (p) => (p.prices?.best ? Number(p.prices.best.total_azn) : Infinity);

export default function Laptops() {
  const { lang, t } = useLang();
  const [laptops, setLaptops] = useState([]);
  const [settings, setSettings] = useState(null);
  const [brand, setBrand] = useState("all");
  const [sort, setSort] = useState("price");
  const [open, setOpen] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getLaptops(lang).then(setLaptops).catch(() => setError(t("err.catalog")));
  }, [lang]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    getSettings().then(setSettings).catch(() => {});
  }, []);

  const brands = useMemo(() => [...new Set(laptops.map((l) => l.brand))].sort(), [laptops]);
  const list = useMemo(() => {
    const f = brand === "all" ? laptops : laptops.filter((l) => l.brand === brand);
    return [...f].sort((a, b) => (sort === "price" ? cost(a) - cost(b) : b.cpu_score + b.gpu_score - (a.cpu_score + a.gpu_score)));
  }, [laptops, brand, sort]);

  return (
    <section className="panel">
      <Heading title={t("catalog.laptops.title")} hint={t("catalog.laptops.hint")} />
      {error && <p role="alert" className="mb-4 rounded-2xl border border-rose-500/30 bg-rose-500/10 px-5 py-4 text-sm text-rose-200">{error}</p>}

      <div className="mb-4 flex flex-wrap items-center gap-2">
        <div className="flex max-w-full gap-2 overflow-x-auto pb-1">
          <Chip active={brand === "all"} onClick={() => setBrand("all")}>{t("catalog.all")}</Chip>
          {brands.map((b) => (
            <Chip key={b} active={brand === b} onClick={() => setBrand(b)}>{b}</Chip>
          ))}
        </div>
        <div className="ml-auto flex items-center gap-3 text-sm text-mist">
          <span className="num">{t("catalog.count", { n: list.length })}</span>
          <SortSelect value={sort} onChange={setSort} />
        </div>
      </div>

      <div className="mb-6 grid gap-4 md:grid-cols-2">
        <Explain />
        <CostLegend settings={settings} />
      </div>

      {list.length === 0 && <p className="text-mist">{t("catalog.empty")}</p>}

      <ul className="grid gap-4 lg:grid-cols-2">
        {list.map((l) => {
          const isOpen = open === l.id;
          const best = l.prices?.best;
          return (
            <li key={l.id} className={`glass rounded-2xl p-5 ${isOpen ? "lg:col-span-2" : ""}`}>
              <p className="text-sm text-mist">{l.brand}</p>
              <h3 className="font-display text-xl font-semibold leading-tight text-snow sm:text-2xl">{l.name}</h3>
              <p className="mt-1 text-sm text-mist">
                {l.screen}, {t("spec.weight", { kg: Number(l.weight_kg).toLocaleString("tr-TR") })}
              </p>
              <div className="mt-4">
                <SpecChips laptop={l} />
              </div>
              <p className="mt-4 text-sm">
                <span className="text-mist">{t("catalog.fits")}: </span>
                <span className="text-snow">{fitsText(t, l.fits)}</span>
              </p>
              <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
                <span className="num font-display text-lg font-semibold text-snow">
                  {best ? (
                    <>
                      {t("catalog.from", { price: azn(best.total_azn) })} <span className="text-sm font-normal text-mist">({best.store})</span>
                    </>
                  ) : (
                    <span className="text-sm font-normal text-mist">{t("catalog.noPrice")}</span>
                  )}
                </span>
                <button type="button" onClick={() => setOpen(isOpen ? null : l.id)} className={btnGhost} aria-expanded={isOpen}>
                  {isOpen ? t("btn.hide") : t("btn.details")} {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </button>
              </div>
              {isOpen && (
                <div className="mt-5">
                  <PriceCompare prices={l.prices} settings={settings} />
                </div>
              )}
            </li>
          );
        })}
      </ul>
      <p className="mt-6 text-xs text-mist">{t("footnote")}</p>
    </section>
  );
}
