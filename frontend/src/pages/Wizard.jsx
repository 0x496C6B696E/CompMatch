import { useEffect, useMemo, useState } from "react";
import { ArrowLeft, ArrowRight, RotateCcw } from "lucide-react";
import { getProfessions, getPrograms, postMatch } from "../api.js";
import { useLang } from "../i18n/index.jsx";
import Stepper from "../components/Stepper.jsx";
import SelectCard from "../components/SelectCard.jsx";
import RequirementBars, { FIELDS } from "../components/RequirementBars.jsx";
import LaptopResults from "../components/LaptopResults.jsx";
import PcResults from "../components/PcResults.jsx";
import Explain from "../components/Explain.jsx";
import { CostLegend } from "../components/PriceCompare.jsx";
import { FIELD_LABEL } from "../lib/levels.js";

export const btnPrimary =
  "inline-flex items-center gap-2 whitespace-nowrap rounded-xl bg-indigo-p px-5 py-2.5 text-sm font-semibold text-white shadow-[0_0_18px_rgba(99,102,241,0.35)] transition-all duration-300 hover:-translate-y-0.5 hover:shadow-[0_0_28px_rgba(99,102,241,0.55)] disabled:opacity-40 disabled:shadow-none disabled:hover:translate-y-0";
export const btnGhost =
  "inline-flex items-center gap-2 whitespace-nowrap rounded-xl glass px-4 py-2.5 text-sm font-medium text-mist transition-colors duration-300 hover:bg-white/[0.06] hover:text-snow";

export function Heading({ title, hint }) {
  return (
    <div className="mb-7">
      <h2 className="font-display text-3xl font-semibold leading-[1.05] tracking-[-0.01em] text-snow sm:text-[2.6rem]">{title}</h2>
      {hint && <p className="mt-2 max-w-[60ch] text-base text-mist">{hint}</p>}
    </div>
  );
}

/** Program kartındaki küçük "parmak izi": programın önerilen değerleri katalog maksimumuna oranla. */
function Fingerprint({ program, programs }) {
  return (
    <div className="mt-4 grid w-full grid-cols-4 gap-1.5" aria-hidden="true">
      {FIELDS.map((f) => {
        const max = Math.max(1, ...programs.map((p) => p[`rec_${f}`]));
        return (
          <div key={f}>
            <div className="h-1 rounded-full bg-white/[0.07]">
              <div className="h-full rounded-full bg-purple-p/70" style={{ width: `${(program[`rec_${f}`] / max) * 100}%` }} />
            </div>
            <div className="mt-1 text-[11px] text-mist">{FIELD_LABEL[f]}</div>
          </div>
        );
      })}
    </div>
  );
}

/** Listeyi `key` ile gruplar; grupsuzlar sona. */
function groupBy(items, key) {
  const map = new Map();
  for (const it of items) {
    const g = it[key];
    const id = g?.id ?? "none";
    if (!map.has(id)) map.set(id, { id, name: g?.name ?? "", order: g?.order ?? 999, icon: g?.icon, items: [] });
    map.get(id).items.push(it);
  }
  return [...map.values()].sort((a, b) => a.order - b.order);
}

export default function Wizard() {
  const { lang, t } = useLang();
  const [step, setStep] = useState(0);
  const [professions, setProfessions] = useState([]);
  const [profession, setProfession] = useState(null);
  const [programs, setPrograms] = useState([]);
  const [selected, setSelected] = useState(new Set());
  const [deviceType, setDeviceType] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Dil değişince adlar değişir: listeleri yeniden çek, seçimleri id ile koru.
  useEffect(() => {
    getProfessions(lang)
      .then((list) => {
        setProfessions(list);
        setProfession((p) => (p ? list.find((x) => x.id === p.id) ?? p : p));
      })
      .catch(() => setError(t("err.backend")));
  }, [lang]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    setPrograms([]);
    setSelected(new Set());
  }, [profession?.id]);

  useEffect(() => {
    if (!profession) return;
    getPrograms(profession.id, lang).then(setPrograms).catch(() => setError(t("err.programs")));
  }, [profession?.id, lang]); // eslint-disable-line react-hooks/exhaustive-deps

  const selectedPrograms = useMemo(() => programs.filter((p) => selected.has(p.id)), [programs, selected]);
  const professionGroups = useMemo(() => groupBy(professions, "category"), [professions]);
  const programGroups = useMemo(() => groupBy(programs, "group"), [programs]);

  const toggleProgram = (id) =>
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });

  const runMatch = async () => {
    setLoading(true);
    setError(null);
    try {
      setResult(await postMatch([...selected], deviceType, lang));
      setStep(3);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (e) {
      setError(e.response?.data?.detail ?? t("err.match"));
    } finally {
      setLoading(false);
    }
  };

  const go = (n) => {
    setStep(n);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const reset = () => {
    go(0);
    setProfession(null);
    setSelected(new Set());
    setDeviceType(null);
    setResult(null);
    setError(null);
  };

  const canNext = [Boolean(profession), selected.size > 0, Boolean(deviceType)][step];

  return (
    <>
      <Stepper current={step} />

      {error && (
        <div role="alert" className="mt-6 rounded-2xl border border-rose-500/30 bg-rose-500/10 px-5 py-4 text-sm text-rose-200">
          {error}
        </div>
      )}

      {/* key=step: adım değişiminde tek panel geçişi */}
      <section key={step} className="panel mt-10">
        {step === 0 && (
          <>
            <Heading title={t("step1.title")} hint={t("step1.hint")} />
            <div className="space-y-8">
              {professionGroups.map((g) => (
                <div key={g.id}>
                  <h3 className="mb-3 font-display text-lg font-semibold text-mist">{g.name}</h3>
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {g.items.map((p) => (
                      <SelectCard
                        key={p.id}
                        icon={p.icon}
                        title={p.name}
                        subtitle={p.description}
                        selected={profession?.id === p.id}
                        onClick={() => setProfession(p)}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}

        {step === 1 && (
          <>
            <Heading title={t("step2.title")} hint={t("step2.hint")} />
            <div className="grid gap-6 lg:grid-cols-[1fr_22rem]">
              <div className="space-y-8">
                {programs.length === 0 && <p className="text-mist">{t("step2.empty")}</p>}
                {programGroups.map((g) => (
                  <div key={g.id}>
                    {g.name && <h3 className="mb-3 font-display text-lg font-semibold text-mist">{g.name}</h3>}
                    <div className="grid content-start gap-4 sm:grid-cols-2">
                      {g.items.map((p) => (
                        <SelectCard key={p.id} icon={p.icon} title={p.name} subtitle={p.blurb} tone="purple" selected={selected.has(p.id)} onClick={() => toggleProgram(p.id)}>
                          <Fingerprint program={p} programs={programs} />
                        </SelectCard>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
              <div className="space-y-4 lg:sticky lg:top-6 lg:self-start">
                <RequirementBars programs={programs} selected={selectedPrograms} hint={t("req.hint.live")} />
                <Explain />
              </div>
            </div>
          </>
        )}

        {step === 2 && (
          <>
            <Heading title={t("step3.title")} hint={t("step3.hint")} />
            <div className="grid gap-4 sm:grid-cols-2">
              <SelectCard icon="Laptop" tone="cyan" title={t("device.laptop.title")} subtitle={t("device.laptop.sub")} selected={deviceType === "laptop"} onClick={() => setDeviceType("laptop")} />
              <SelectCard icon="Monitor" tone="purple" title={t("device.pc.title")} subtitle={t("device.pc.sub")} selected={deviceType === "pc"} onClick={() => setDeviceType("pc")} />
            </div>
          </>
        )}

        {step === 3 && result && (
          <>
            <Heading
              title={result.device_type === "laptop" ? t("step4.laptop.title") : t("step4.pc.title")}
              hint={t("step4.hint", { profession: profession?.name ?? "", programs: selectedPrograms.map((p) => p.name).join(", ") })}
            />
            <div className="space-y-6">
              <RequirementBars programs={programs} selected={selectedPrograms} requirements={result.requirements} hint={t("req.hint.result")} />
              <div className="grid gap-4 md:grid-cols-2">
                <Explain />
                <CostLegend settings={result.settings} />
              </div>
              {result.device_type === "laptop" ? (
                <LaptopResults laptops={result.laptops} settings={result.settings} />
              ) : (
                <PcResults components={result.components} settings={result.settings} />
              )}
              <p className="text-xs text-mist">{t("footnote")}</p>
            </div>
          </>
        )}
      </section>

      <footer className="mt-10 flex items-center justify-between gap-3">
        <button type="button" onClick={() => go(Math.max(0, step - 1))} className={btnGhost} style={{ visibility: step === 0 ? "hidden" : "visible" }}>
          <ArrowLeft size={16} /> {t("btn.back")}
        </button>
        {step < 2 && (
          <button type="button" onClick={() => go(step + 1)} disabled={!canNext} className={btnPrimary}>
            {t("btn.next")} <ArrowRight size={16} />
          </button>
        )}
        {step === 2 && (
          <button type="button" onClick={runMatch} disabled={!canNext || loading} className={btnPrimary}>
            {loading ? t("btn.computing") : t("btn.match")} <ArrowRight size={16} />
          </button>
        )}
        {step === 3 && (
          <button type="button" onClick={reset} className={btnPrimary}>
            <RotateCcw size={16} /> {t("btn.newMatch")}
          </button>
        )}
      </footer>
    </>
  );
}
