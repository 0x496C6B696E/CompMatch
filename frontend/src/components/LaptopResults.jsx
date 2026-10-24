import { Crown, Laptop as LaptopIcon, Rocket, Weight, Zap } from "lucide-react";
import PriceCompare from "./PriceCompare.jsx";

const TIER = {
  value: { icon: Zap, tone: "from-cyan-p to-indigo-p", text: "text-cyan-300" },
  recommended: { icon: Crown, tone: "from-indigo-p to-purple-p", text: "text-indigo-300" },
  pro: { icon: Rocket, tone: "from-purple-p to-pink-500", text: "text-purple-300" },
};

function Spec({ label, value }) {
  return (
    <div className="rounded-xl bg-white/[0.03] px-3 py-2">
      <div className="text-[11px] uppercase tracking-wider text-slate-500">{label}</div>
      <div className="truncate text-sm text-slate-200" title={value}>
        {value}
      </div>
    </div>
  );
}

export default function LaptopResults({ laptops, settings }) {
  if (!laptops?.length) {
    return <p className="glass rounded-2xl p-6 text-slate-400">Gereksinimleri karşılayan laptop bulunamadı.</p>;
  }
  return (
    <div className="space-y-6">
      {laptops.map(({ tier, label, laptop, meets, prices }, i) => {
        const t = TIER[tier];
        const TI = t.icon;
        return (
          <article
            key={laptop.id}
            className="glass rounded-2xl p-6 animate-rise"
            style={{ animationDelay: `${i * 90}ms` }}
          >
            <header className="mb-5 flex flex-wrap items-start justify-between gap-4">
              <div className="flex items-start gap-4">
                <span
                  className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${t.tone} text-white shadow-[0_0_20px_rgba(99,102,241,0.35)]`}
                >
                  <TI size={22} />
                </span>
                <div>
                  <div className={`text-xs font-semibold uppercase tracking-wider ${t.text}`}>
                    {i + 1}. {label}
                  </div>
                  <h3 className="text-lg font-semibold text-white">{laptop.name}</h3>
                  <p className="text-sm text-slate-400">
                    {laptop.brand} · {laptop.screen}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span
                  className={`rounded-full px-2.5 py-1 font-medium ${
                    meets === "rec" ? "bg-green-p/15 text-green-p" : "bg-cyan-p/15 text-cyan-300"
                  }`}
                >
                  {meets === "rec" ? "Önerilen gereksinimi karşılıyor" : "Minimum gereksinimi karşılıyor"}
                </span>
                <span className="inline-flex items-center gap-1 rounded-full bg-white/[0.04] px-2.5 py-1 text-slate-400">
                  <Weight size={12} /> {Number(laptop.weight_kg).toFixed(2)} kg
                </span>
              </div>
            </header>

            <div className="mb-5 grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
              <Spec label="CPU" value={laptop.cpu} />
              <Spec label="GPU" value={laptop.gpu} />
              <Spec label="RAM" value={`${laptop.ram_gb} GB`} />
              <Spec label="SSD" value={`${laptop.ssd_gb} GB`} />
              <Spec label="CPU skoru" value={laptop.cpu_score.toLocaleString("tr-TR")} />
              <Spec label="GPU skoru" value={laptop.gpu_score.toLocaleString("tr-TR")} />
            </div>

            <PriceCompare prices={prices} settings={settings} />
          </article>
        );
      })}
      <p className="flex items-center gap-2 text-xs text-slate-500">
        <LaptopIcon size={14} /> Fiyatlar admin panelinden girilen örnek verilerdir; mağaza linkleri arama sayfasına gider.
      </p>
    </div>
  );
}
