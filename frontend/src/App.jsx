import { useEffect, useMemo, useState } from "react";
import { ArrowLeft, ArrowRight, RotateCcw } from "lucide-react";
import { getProfessions, getPrograms, postMatch } from "./api.js";
import Stepper from "./components/Stepper.jsx";
import SelectCard from "./components/SelectCard.jsx";
import RequirementBars, { FIELDS } from "./components/RequirementBars.jsx";
import LaptopResults from "./components/LaptopResults.jsx";
import PcResults from "./components/PcResults.jsx";
import { CostLegend } from "./components/PriceCompare.jsx";

const btnPrimary =
  "inline-flex items-center gap-2 rounded-xl bg-indigo-p px-5 py-2.5 text-sm font-semibold text-white shadow-[0_0_18px_rgba(99,102,241,0.35)] transition-all duration-300 hover:-translate-y-0.5 hover:shadow-[0_0_28px_rgba(99,102,241,0.55)] disabled:opacity-40 disabled:shadow-none disabled:hover:translate-y-0";
const btnGhost =
  "inline-flex items-center gap-2 whitespace-nowrap rounded-xl glass px-4 py-2.5 text-sm font-medium text-mist transition-colors duration-300 hover:bg-white/[0.06] hover:text-snow";

function Heading({ title, hint }) {
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
        const max = Math.max(1, ...programs.map((p) => p[`rec_${f.key}`]));
        return (
          <div key={f.key} title={`${f.label}: ${f.fmt(program[`rec_${f.key}`])}`}>
            <div className="h-1 rounded-full bg-white/[0.07]">
              <div className="h-full rounded-full bg-purple-p/70" style={{ width: `${(program[`rec_${f.key}`] / max) * 100}%` }} />
            </div>
            <div className="mt-1 text-[11px] text-mist">{f.label.replace(" skoru", "")}</div>
          </div>
        );
      })}
    </div>
  );
}

export default function App() {
  const [step, setStep] = useState(0);
  const [professions, setProfessions] = useState([]);
  const [profession, setProfession] = useState(null);
  const [programs, setPrograms] = useState([]);
  const [selected, setSelected] = useState(new Set());
  const [deviceType, setDeviceType] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    getProfessions()
      .then(setProfessions)
      .catch(() => setError("Sunucuya bağlanamadık. Django'nun 8000 portunda çalıştığını kontrol et."));
  }, []);

  useEffect(() => {
    if (!profession) return;
    setPrograms([]);
    setSelected(new Set());
    getPrograms(profession.id).then(setPrograms).catch(() => setError("Programlar yüklenemedi."));
  }, [profession]);

  const selectedPrograms = useMemo(() => programs.filter((p) => selected.has(p.id)), [programs, selected]);

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
      setResult(await postMatch([...selected], deviceType));
      setStep(3);
    } catch (e) {
      setError(e.response?.data?.detail ?? "Eşleştirme yapılamadı. Tekrar dene.");
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setStep(0);
    setProfession(null);
    setSelected(new Set());
    setDeviceType(null);
    setResult(null);
    setError(null);
  };

  const canNext = [Boolean(profession), selected.size > 0, Boolean(deviceType)][step];

  return (
    <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
      <header className="mb-6 flex items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-bold leading-none tracking-[-0.02em] text-snow">CompMatch</h1>
          <p className="mt-1.5 text-sm text-mist">Mesleğine göre donanım, Bakü'ye göre fiyat.</p>
        </div>
        {step > 0 && (
          <button type="button" onClick={reset} className={btnGhost}>
            <RotateCcw size={16} /> Baştan başla
          </button>
        )}
      </header>

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
            <Heading title="Ne iş yapıyorsun?" hint="Mesleğini seç, kullandığın programları ona göre listeleyelim." />
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-6">
              {professions.map((p, i) => (
                <SelectCard
                  key={p.id}
                  icon={p.icon}
                  title={p.name}
                  subtitle={p.description}
                  selected={profession?.id === p.id}
                  onClick={() => setProfession(p)}
                  className={i < 3 ? "lg:col-span-2" : "lg:col-span-3"}
                />
              ))}
            </div>
          </>
        )}

        {step === 1 && (
          <>
            <Heading
              title="Hangi programları kullanıyorsun?"
              hint="Birden fazla seçebilirsin. Her bileşen için seçtiklerinin en yükseği alınır, böylece hiçbiri darboğaz yaratmaz."
            />
            <div className="grid gap-6 lg:grid-cols-[1fr_22rem]">
              <div className="grid content-start gap-4 sm:grid-cols-2">
                {programs.length === 0 && (
                  <p className="text-mist sm:col-span-2">Bu meslek için henüz program eklenmedi. Admin panelinden ekleyebilirsin.</p>
                )}
                {programs.map((p) => (
                  <SelectCard key={p.id} icon={p.icon} title={p.name} tone="purple" selected={selected.has(p.id)} onClick={() => toggleProgram(p.id)}>
                    <Fingerprint program={p} programs={programs} />
                  </SelectCard>
                ))}
              </div>
              <div className="lg:sticky lg:top-6 lg:self-start">
                <RequirementBars
                  programs={programs}
                  selected={selectedPrograms}
                  title="Sistem gereksinimi"
                  hint="Program seçtikçe güncellenir."
                />
              </div>
            </div>
          </>
        )}

        {step === 2 && (
          <>
            <Heading title="Laptop mı, toplama PC mi?" hint="Laptop için üç öneri, PC için birbiriyle uyumlu parça listesi hazırlarız." />
            <div className="grid gap-4 sm:grid-cols-2">
              <SelectCard
                icon="Laptop"
                tone="cyan"
                title="Laptop"
                subtitle="Taşınabilir. Fiyat/performans, tam uyumlu ve üst segment olmak üzere üç seçenek."
                selected={deviceType === "laptop"}
                onClick={() => setDeviceType("laptop")}
              />
              <SelectCard
                icon="Monitor"
                tone="purple"
                title="Masaüstü PC (toplama)"
                subtitle="İşlemci, ekran kartı, anakart, RAM, SSD ve kasa+PSU. Soket, RAM tipi ve güç uyumu kontrol edilir."
                selected={deviceType === "pc"}
                onClick={() => setDeviceType("pc")}
              />
            </div>
          </>
        )}

        {step === 3 && result && (
          <>
            <Heading
              title={result.device_type === "laptop" ? "Sana uygun 3 laptop" : "Uyumlu PC parçaları"}
              hint={`${profession?.name} için ${selectedPrograms.map((p) => p.name).join(", ")}.`}
            />
            <div className="space-y-6">
              <RequirementBars
                programs={programs}
                selected={selectedPrograms}
                requirements={result.requirements}
                title="Sistem gereksinimi"
                hint="Her bileşen için en yüksek değer alındı. Tikler seçtiğin programların tek tek ihtiyacını gösterir."
              />
              <CostLegend settings={result.settings} />
              {result.device_type === "laptop" ? (
                <LaptopResults laptops={result.laptops} settings={result.settings} />
              ) : (
                <PcResults components={result.components} settings={result.settings} />
              )}
              <p className="text-xs text-mist">Fiyatlar admin panelinden girilen örnek verilerdir; mağaza linkleri arama sayfasına gider.</p>
            </div>
          </>
        )}
      </section>

      <footer className="mt-10 flex items-center justify-between">
        <button
          type="button"
          onClick={() => setStep((s) => Math.max(0, s - 1))}
          className={btnGhost}
          style={{ visibility: step === 0 ? "hidden" : "visible" }}
        >
          <ArrowLeft size={16} /> Geri
        </button>
        {step < 2 && (
          <button type="button" onClick={() => setStep(step + 1)} disabled={!canNext} className={btnPrimary}>
            Devam <ArrowRight size={16} />
          </button>
        )}
        {step === 2 && (
          <button type="button" onClick={runMatch} disabled={!canNext || loading} className={btnPrimary}>
            {loading ? "Hesaplanıyor…" : "Sistemi öner"} <ArrowRight size={16} />
          </button>
        )}
        {step === 3 && (
          <button type="button" onClick={reset} className={btnPrimary}>
            <RotateCcw size={16} /> Yeni eşleştirme
          </button>
        )}
      </footer>
    </main>
  );
}
