import { useEffect, useState } from "react";
import { ArrowLeft, ArrowRight, Laptop, Monitor, RotateCcw, Sparkles } from "lucide-react";
import { getProfessions, getPrograms, postMatch } from "./api.js";
import Stepper from "./components/Stepper.jsx";
import SelectCard from "./components/SelectCard.jsx";
import RequirementsCard from "./components/RequirementsCard.jsx";
import LaptopResults from "./components/LaptopResults.jsx";
import PcResults from "./components/PcResults.jsx";

const btnPrimary =
  "inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-p to-purple-p px-5 py-2.5 text-sm font-semibold text-white shadow-[0_0_20px_rgba(99,102,241,0.35)] transition-all duration-300 hover:-translate-y-0.5 hover:shadow-[0_0_28px_rgba(168,85,247,0.45)] disabled:opacity-40 disabled:hover:translate-y-0 disabled:hover:shadow-none";
const btnGhost =
  "inline-flex items-center gap-2 rounded-xl glass px-4 py-2.5 text-sm font-medium text-slate-300 transition-all duration-300 hover:bg-white/[0.06] hover:text-white";

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
      .catch(() => setError("Backend'e ulaşılamadı. Django sunucusu localhost:8000 üzerinde çalışıyor mu?"));
  }, []);

  useEffect(() => {
    if (!profession) return;
    setPrograms([]);
    setSelected(new Set());
    getPrograms(profession.id).then(setPrograms).catch(() => setError("Programlar yüklenemedi."));
  }, [profession]);

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
      setError(e.response?.data?.detail ?? "Eşleştirme sırasında hata oluştu.");
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
    <div className="relative min-h-screen overflow-x-hidden">
      {/* Uzay atmosferi: iki yumuşak neon leke */}
      <div className="pointer-events-none fixed inset-0 -z-10">
        <div className="absolute -top-40 -left-32 h-[32rem] w-[32rem] rounded-full bg-indigo-p/20 blur-[140px]" />
        <div className="absolute top-1/3 -right-40 h-[28rem] w-[28rem] rounded-full bg-purple-p/15 blur-[140px]" />
        <div className="absolute bottom-0 left-1/3 h-[20rem] w-[20rem] rounded-full bg-cyan-p/10 blur-[120px]" />
      </div>

      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
        <header className="mb-8 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-p to-purple-p text-white shadow-[0_0_24px_rgba(99,102,241,0.45)]">
              <Sparkles size={22} />
            </span>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white">CompMatch</h1>
              <p className="text-xs text-slate-400">Donanım eşleştirme · Bakü vs Global maliyet</p>
            </div>
          </div>
          {step > 0 && (
            <button type="button" onClick={reset} className={btnGhost}>
              <RotateCcw size={16} /> Baştan başla
            </button>
          )}
        </header>

        <Stepper current={step} />

        {error && (
          <div className="mt-6 rounded-2xl border border-rose-500/30 bg-rose-500/10 px-5 py-4 text-sm text-rose-200">
            {error}
          </div>
        )}

        <section className="mt-8">
          {step === 0 && (
            <div className="animate-rise">
              <h2 className="mb-1 text-2xl font-semibold text-white">Ne iş yapıyorsun?</h2>
              <p className="mb-6 text-slate-400">Mesleğini seç; kullandığın programları ona göre listeleyelim.</p>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {professions.map((p) => (
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
          )}

          {step === 1 && (
            <div className="animate-rise">
              <h2 className="mb-1 text-2xl font-semibold text-white">Hangi programları kullanıyorsun?</h2>
              <p className="mb-6 text-slate-400">
                Birden fazla seçebilirsin. Gereksinimler, seçtiklerinin en yükseği baz alınarak hesaplanır.
              </p>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {programs.map((p) => (
                  <SelectCard
                    key={p.id}
                    icon={p.icon}
                    title={p.name}
                    accent="purple"
                    selected={selected.has(p.id)}
                    onClick={() => toggleProgram(p.id)}
                  >
                    <div className="mt-2 flex flex-wrap gap-1.5 text-[11px] text-slate-500">
                      <span className="rounded-md bg-white/[0.04] px-1.5 py-0.5">Önerilen RAM {p.rec_ram_gb} GB</span>
                      <span className="rounded-md bg-white/[0.04] px-1.5 py-0.5">GPU {p.rec_gpu_score.toLocaleString("tr-TR")}</span>
                    </div>
                  </SelectCard>
                ))}
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="animate-rise">
              <h2 className="mb-1 text-2xl font-semibold text-white">Laptop mu, masaüstü PC mi?</h2>
              <p className="mb-6 text-slate-400">Laptop için 3 öneri, PC için birbiriyle uyumlu parça listesi hazırlarız.</p>
              <div className="grid gap-4 sm:grid-cols-2">
                <SelectCard
                  icon="Laptop"
                  accent="cyan"
                  title="Laptop"
                  subtitle="Taşınabilir. Fiyat/Performans, Önerilen ve Pro olmak üzere 3 seçenek."
                  selected={deviceType === "laptop"}
                  onClick={() => setDeviceType("laptop")}
                />
                <SelectCard
                  icon="Monitor"
                  accent="purple"
                  title="Masaüstü PC (Toplama)"
                  subtitle="CPU, GPU, anakart, RAM, SSD ve kasa+PSU. Soket, RAM tipi ve güç uyumu kontrol edilir."
                  selected={deviceType === "pc"}
                  onClick={() => setDeviceType("pc")}
                />
              </div>
            </div>
          )}

          {step === 3 && result && (
            <div className="space-y-6">
              <div className="flex flex-wrap items-end justify-between gap-3">
                <div>
                  <h2 className="text-2xl font-semibold text-white">
                    {result.device_type === "laptop" ? "Sana uygun 3 laptop" : "Uyumlu PC bileşenleri"}
                  </h2>
                  <p className="text-slate-400">
                    {profession?.name} · {selected.size} program · {result.device_type === "laptop" ? <Laptop className="inline" size={14} /> : <Monitor className="inline" size={14} />}
                  </p>
                </div>
              </div>
              <RequirementsCard requirements={result.requirements} />
              {result.device_type === "laptop" ? (
                <LaptopResults laptops={result.laptops} settings={result.settings} />
              ) : (
                <PcResults components={result.components} settings={result.settings} />
              )}
            </div>
          )}
        </section>

        {/* Navigasyon */}
        <footer className="mt-10 flex items-center justify-between">
          <button
            type="button"
            onClick={() => setStep((s) => Math.max(0, s - 1))}
            className={btnGhost}
            disabled={step === 0}
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
              {loading ? "Hesaplanıyor…" : "Sistemi Öner"} <Sparkles size={16} />
            </button>
          )}
          {step === 3 && (
            <button type="button" onClick={reset} className={btnPrimary}>
              <RotateCcw size={16} /> Yeni eşleştirme
            </button>
          )}
        </footer>
      </main>
    </div>
  );
}
