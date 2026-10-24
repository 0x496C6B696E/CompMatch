import { Cpu, Gauge, HardDrive, MemoryStick } from "lucide-react";

const ROWS = [
  { key: "cpu_score", label: "CPU skoru", icon: Cpu, fmt: (v) => v.toLocaleString("tr-TR") },
  { key: "gpu_score", label: "GPU skoru", icon: Gauge, fmt: (v) => v.toLocaleString("tr-TR") },
  { key: "ram_gb", label: "RAM", icon: MemoryStick, fmt: (v) => `${v} GB` },
  { key: "ssd_gb", label: "SSD", icon: HardDrive, fmt: (v) => `${v} GB` },
];

/** Seçilen programların MAX değerlerinden türeyen Min / Önerilen gereksinim kartı. */
export default function RequirementsCard({ requirements }) {
  const { min, rec } = requirements;
  return (
    <section className="glass rounded-2xl p-6 animate-rise">
      <header className="mb-5 flex items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-white">Sistem Gereksinimleri</h2>
          <p className="text-sm text-slate-400">
            Seçtiğin programlar arasındaki en yüksek değerler alındı; hiçbir program darboğaz yaratmaz.
          </p>
        </div>
      </header>
      <div className="grid grid-cols-[1fr_auto_auto] gap-x-6 gap-y-3 text-sm">
        <span className="text-slate-500 text-xs uppercase tracking-wider">Bileşen</span>
        <span className="text-right text-xs uppercase tracking-wider text-cyan-300">Minimum</span>
        <span className="text-right text-xs uppercase tracking-wider text-indigo-300">Önerilen</span>
        {ROWS.map(({ key, label, icon: I, fmt }) => (
          <div key={key} className="contents">
            <span className="flex items-center gap-2 text-slate-300">
              <I size={16} className="text-slate-500" /> {label}
            </span>
            <span className="text-right font-mono text-cyan-200">{fmt(min[key])}</span>
            <span className="text-right font-mono font-semibold text-white">{fmt(rec[key])}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
