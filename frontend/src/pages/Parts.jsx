import { useEffect, useMemo, useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { azn, getComponents, getSettings } from "../api.js";
import { useLang } from "../i18n/index.jsx";
import { componentLevelField, componentSpec, fitsText } from "../lib/spec.js";
import PriceCompare, { CostLegend } from "../components/PriceCompare.jsx";
import { LevelPill } from "../components/SpecChips.jsx";
import { Chip, SortSelect } from "./Laptops.jsx";
import { Heading, btnGhost } from "./Wizard.jsx";

const CATEGORIES = ["cpu", "gpu", "motherboard", "ram", "ssd", "case_psu"];
const cost = (p) => (p.prices?.best ? Number(p.prices.best.total_azn) : Infinity);
const perf = (c) => c.score || c.capacity_gb || c.psu_watts || 0;

export default function Parts() {
  const { lang, t } = useLang();
  const [components, setComponents] = useState([]);
  const [settings, setSettings] = useState(null);
  const [category, setCategory] = useState("cpu");
  const [brand, setBrand] = useState("all");
  const [sort, setSort] = useState("price");
  const [open, setOpen] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getComponents(lang).then(setComponents).catch(() => setError(t("err.catalog")));
  }, [lang]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    getSettings().then(setSettings).catch(() => {});
  }, []);

  const inCategory = useMemo(() => components.filter((c) => c.category === category), [components, category]);
  const brands = useMemo(() => [...new Set(inCategory.map((c) => c.brand))].sort(), [inCategory]);
  const list = useMemo(() => {
    const f = brand === "all" ? inCategory : inCategory.filter((c) => c.brand === brand);
    return [...f].sort((a, b) => (sort === "price" ? cost(a) - cost(b) : perf(b) - perf(a)));
  }, [inCategory, brand, sort]);

  const pickCategory = (c) => {
    setCategory(c);
    setBrand("all");
    setOpen(null);
  };

  return (
    <section className="panel">
      <Heading title={t("catalog.pc.title")} hint={t("catalog.pc.hint")} />
      {error && <p role="alert" className="mb-4 rounded-2xl border border-rose-500/30 bg-rose-500/10 px-5 py-4 text-sm text-rose-200">{error}</p>}

      <div className="mb-4 flex gap-2 overflow-x-auto pb-1" role="tablist">
        {CATEGORIES.map((c) => (
          <Chip key={c} active={category === c} onClick={() => pickCategory(c)}>{t(`cat.${c}`)}</Chip>
        ))}
      </div>
      <p className="mb-5 max-w-[60ch] rounded-xl border border-indigo-p/30 bg-indigo-p/10 px-4 py-3 text-sm leading-relaxed text-snow">
        {t(`cat.${category}.explain`)}
      </p>

      <div className="mb-6 flex flex-wrap items-center gap-2">
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

      <div className="mb-6">
        <CostLegend settings={settings} />
      </div>

      {list.length === 0 && <p className="text-mist">{t("catalog.empty")}</p>}

      <ul className="grid gap-4 lg:grid-cols-2">
        {list.map((c) => {
          const isOpen = open === c.id;
          const best = c.prices?.best;
          const lvl = componentLevelField(c);
          return (
            <li key={c.id} className={`glass rounded-2xl p-5 ${isOpen ? "lg:col-span-2" : ""}`}>
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm text-mist">{c.brand}</p>
                  <h3 className="font-display text-xl font-semibold leading-tight text-snow sm:text-2xl">{c.name}</h3>
                  <p className="num mt-1 text-sm text-mist">{componentSpec(t, c)}</p>
                </div>
                {lvl && <LevelPill field={lvl[0]} value={lvl[1]} />}
              </div>
              {lvl && (
                <p className="mt-3 text-sm">
                  <span className="text-mist">{t("catalog.fits")}: </span>
                  <span className="text-snow">{fitsText(t, c.fits)}</span>
                </p>
              )}
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
                <button type="button" onClick={() => setOpen(isOpen ? null : c.id)} className={btnGhost} aria-expanded={isOpen}>
                  {isOpen ? t("btn.hide") : t("btn.details")} {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </button>
              </div>
              {isOpen && (
                <div className="mt-5">
                  <PriceCompare prices={c.prices} settings={settings} />
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
