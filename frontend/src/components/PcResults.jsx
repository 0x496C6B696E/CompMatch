import { azn } from "../api.js";
import PriceCompare from "./PriceCompare.jsx";

function specLine(c) {
  const bits = [];
  if (c.score) bits.push(`skor ${c.score.toLocaleString("tr-TR")}`);
  if (c.capacity_gb) bits.push(`${c.capacity_gb} GB`);
  if (c.socket) bits.push(`${c.socket} soket`);
  if (c.ram_type) bits.push(c.ram_type);
  if (c.tdp_watts) bits.push(`${c.tdp_watts} W`);
  if (c.psu_watts) bits.push(`${c.psu_watts} W PSU`);
  bits.push(`${Number(c.weight_kg).toLocaleString("tr-TR")} kg`);
  return bits.join(", ");
}

const MEETS = {
  rec: ["Önerilen", "bg-green-p/15 text-green-p"],
  min: ["Minimum", "bg-cyan-p/15 text-cyan-300"],
  below: ["Gereksinimin altında", "bg-rose-500/15 text-rose-300"],
};

export default function PcResults({ components, settings }) {
  const found = components.filter((p) => p.component);
  const allLocal = found.reduce((s, p) => s + Number(p.prices?.local?.find((o) => o.in_stock)?.price_azn ?? p.prices?.best?.total_azn ?? 0), 0);
  const bestMix = found.reduce((s, p) => s + Number(p.prices?.best?.total_azn ?? 0), 0);
  const saving = allLocal - bestMix;
  const max = Math.max(allLocal, bestMix, 1);

  return (
    <div className="space-y-6">
      <section className="glass rounded-2xl p-5 sm:p-6">
        <h3 className="font-display text-2xl font-semibold leading-tight text-snow">Toplam maliyet</h3>
        <p className="mt-1 max-w-[60ch] text-sm text-mist">
          {saving > 0
            ? `Her parçayı en karlı yerden alırsan ${azn(saving)} daha az ödersin.`
            : "Tüm parçalar için en karlı yer Bakü."}
        </p>
        <ul className="mt-5 space-y-3">
          <li className="flex items-center gap-3 text-sm">
            <span className="w-44 shrink-0 text-mist">Tümü Bakü'den</span>
            <div className="h-3 flex-1 rounded-sm bg-white/[0.05]">
              <div className="bar-grow h-full rounded-sm bg-cyan-p" style={{ width: `${(allLocal / max) * 100}%` }} />
            </div>
            <span className="num w-24 shrink-0 text-right font-display text-lg font-semibold text-snow">{azn(allLocal)}</span>
          </li>
          <li className="flex items-center gap-3 text-sm">
            <span className="w-44 shrink-0 text-mist">Her parça en karlı yerden</span>
            <div className="h-3 flex-1 rounded-sm bg-white/[0.05]">
              <div className="bar-grow h-full rounded-sm bg-green-p shadow-[0_0_12px_rgba(16,185,129,0.45)]" style={{ width: `${(bestMix / max) * 100}%` }} />
            </div>
            <span className="num w-24 shrink-0 text-right font-display text-lg font-semibold text-snow">{azn(bestMix)}</span>
          </li>
        </ul>
      </section>

      <ol className="space-y-6">
        {components.map(({ category, label, component, meets, compat_note, prices }) => (
          <li key={category} className="glass rounded-2xl p-5 sm:p-6">
            <header className="flex flex-wrap items-start justify-between gap-x-6 gap-y-3">
              <div className="min-w-0">
                <p className="text-sm text-mist">{label}</p>
                {component ? (
                  <>
                    <h3 className="font-display text-2xl font-semibold leading-tight text-snow">{component.name}</h3>
                    <p className="num mt-1 text-sm text-mist">{component.brand}, {specLine(component)}</p>
                  </>
                ) : (
                  <>
                    <h3 className="font-display text-2xl font-semibold leading-tight text-rose-300">Uyumlu parça bulunamadı</h3>
                    <p className="mt-1 text-sm text-mist">Admin panelinden bu kategoriye {compat_note ? `${compat_note} uyumlu ` : ""}bir parça ekle.</p>
                  </>
                )}
              </div>
              {component && (
                <div className="flex shrink-0 flex-wrap gap-2 text-xs">
                  <span className={`rounded-full px-3 py-1 font-medium ${MEETS[meets][1]}`}>{MEETS[meets][0]}</span>
                  {compat_note && <span className="rounded-full bg-purple-p/15 px-3 py-1 text-purple-300">{compat_note}</span>}
                </div>
              )}
            </header>
            {component && (
              <div className="mt-6">
                <PriceCompare prices={prices} settings={settings} />
              </div>
            )}
          </li>
        ))}
      </ol>
    </div>
  );
}
