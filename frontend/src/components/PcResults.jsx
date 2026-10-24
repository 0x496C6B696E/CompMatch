import { Box, CircuitBoard, Cpu, Gauge, HardDrive, MemoryStick, Weight } from "lucide-react";
import { azn } from "../api.js";
import PriceCompare from "./PriceCompare.jsx";

const CAT_ICON = {
  cpu: Cpu,
  gpu: Gauge,
  motherboard: CircuitBoard,
  ram: MemoryStick,
  ssd: HardDrive,
  case_psu: Box,
};

function specLine(c) {
  const bits = [];
  if (c.score) bits.push(`Skor ${c.score.toLocaleString("tr-TR")}`);
  if (c.capacity_gb) bits.push(`${c.capacity_gb} GB`);
  if (c.socket) bits.push(c.socket);
  if (c.ram_type) bits.push(c.ram_type);
  if (c.tdp_watts) bits.push(`${c.tdp_watts} W TDP`);
  if (c.psu_watts) bits.push(`${c.psu_watts} W PSU`);
  return bits.join(" · ");
}

export default function PcResults({ components, settings }) {
  const totalLocal = components.reduce((s, p) => s + Number(p.prices?.local?.find((o) => o.in_stock)?.price_azn ?? 0), 0);
  const totalBest = components.reduce((s, p) => s + Number(p.prices?.best?.total_azn ?? 0), 0);

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-3 animate-rise">
        <div className="glass rounded-2xl p-4">
          <div className="text-xs uppercase tracking-wider text-slate-500">Bileşen sayısı</div>
          <div className="mt-1 text-2xl font-semibold text-white">{components.filter((p) => p.component).length} / 6</div>
        </div>
        <div className="glass rounded-2xl p-4">
          <div className="text-xs uppercase tracking-wider text-cyan-300">Tümü Bakü'den alınırsa</div>
          <div className="mt-1 text-2xl font-semibold text-white font-mono">{azn(totalLocal)}</div>
        </div>
        <div className="glass rounded-2xl p-4 ring-1 ring-green-p/50 bg-green-p/[0.04]">
          <div className="text-xs uppercase tracking-wider text-green-p">Her parça en karlı yerden</div>
          <div className="mt-1 text-2xl font-semibold text-white font-mono">{azn(totalBest)}</div>
          {totalLocal > totalBest && (
            <div className="text-xs text-green-p">{azn(totalLocal - totalBest)} tasarruf</div>
          )}
        </div>
      </div>

      {components.map(({ category, label, component, meets, compat_note, prices }, i) => {
        const I = CAT_ICON[category] ?? Box;
        return (
          <article
            key={category}
            className="glass rounded-2xl p-6 animate-rise"
            style={{ animationDelay: `${i * 70}ms` }}
          >
            <header className="mb-5 flex flex-wrap items-start justify-between gap-4">
              <div className="flex items-start gap-4">
                <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-p/30 to-purple-p/20 text-indigo-300">
                  <I size={22} />
                </span>
                <div>
                  <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">{label}</div>
                  {component ? (
                    <>
                      <h3 className="text-lg font-semibold text-white">{component.name}</h3>
                      <p className="text-sm text-slate-400">
                        {component.brand} · {specLine(component)}
                      </p>
                    </>
                  ) : (
                    <h3 className="text-lg font-semibold text-rose-300">Uyumlu bileşen bulunamadı</h3>
                  )}
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-2 text-xs">
                {component && (
                  <span
                    className={`rounded-full px-2.5 py-1 font-medium ${
                      meets === "rec"
                        ? "bg-green-p/15 text-green-p"
                        : meets === "min"
                          ? "bg-cyan-p/15 text-cyan-300"
                          : "bg-rose-500/15 text-rose-300"
                    }`}
                  >
                    {meets === "rec" ? "Önerilen" : meets === "min" ? "Minimum" : "Gereksinim altı"}
                  </span>
                )}
                {compat_note && (
                  <span className="rounded-full bg-purple-p/15 px-2.5 py-1 text-purple-300">{compat_note}</span>
                )}
                {component && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-white/[0.04] px-2.5 py-1 text-slate-400">
                    <Weight size={12} /> {Number(component.weight_kg).toFixed(2)} kg
                  </span>
                )}
              </div>
            </header>
            {component && <PriceCompare prices={prices} settings={settings} />}
          </article>
        );
      })}
    </div>
  );
}
