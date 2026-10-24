import { ExternalLink, Globe, Store, Trophy } from "lucide-react";
import { azn, usd } from "../api.js";

function Badge({ savings }) {
  return (
    <span className="absolute -top-3 left-4 inline-flex items-center gap-1.5 rounded-full bg-gradient-to-r from-green-p to-emerald-400 px-3 py-1 text-xs font-bold text-space animate-glow">
      <Trophy size={13} />
      En Karlı Seçenek{savings != null && Number(savings) > 0 ? ` (${azn(savings)} Tasarruf)` : ""}
    </span>
  );
}

function Panel({ title, icon: I, best, savings, children, tone }) {
  return (
    <div
      className={`relative glass rounded-2xl p-4 pt-5 transition-all duration-300 ${
        best ? "ring-1 ring-green-p/60 bg-green-p/[0.04]" : ""
      }`}
    >
      {best && <Badge savings={savings} />}
      <h4 className={`mb-3 flex items-center gap-2 text-sm font-semibold ${tone}`}>
        <I size={16} /> {title}
      </h4>
      {children}
    </div>
  );
}

function StoreLink({ store, url }) {
  return url ? (
    <a
      href={url}
      target="_blank"
      rel="noreferrer"
      className="inline-flex items-center gap-1 text-slate-200 hover:text-white underline-offset-2 hover:underline"
    >
      {store} <ExternalLink size={12} className="opacity-60" />
    </a>
  ) : (
    <span>{store}</span>
  );
}

/** Bakü yerel mağazalar vs Global + Azerbaycan gümrük — yan yana Bento kartlar. */
export default function PriceCompare({ prices, settings }) {
  if (!prices) return null;
  const { local, global: glob, best } = prices;
  const bestSide = best?.side;

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Panel
        title="Bakü Yerel Mağazalar"
        icon={Store}
        tone="text-cyan-300"
        best={bestSide === "local"}
        savings={best?.savings_azn}
      >
        {local.length === 0 ? (
          <p className="text-sm text-slate-500">Yerel fiyat kaydı yok.</p>
        ) : (
          <table className="w-full text-sm">
            <tbody>
              {local.map((o) => (
                <tr key={o.store} className="border-t border-white/[0.06] first:border-0">
                  <td className="py-2">
                    <StoreLink store={o.store} url={o.url} />
                  </td>
                  <td className="py-2 text-xs">
                    <span className={o.in_stock ? "text-green-p" : "text-rose-400"}>
                      {o.in_stock ? "Stokta" : "Stok yok"}
                    </span>
                  </td>
                  <td className="py-2 text-right font-mono font-semibold text-white">{azn(o.price_azn)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Panel>

      <Panel
        title="Global + Azerbaycan Gümrük Hesabı"
        icon={Globe}
        tone="text-purple-300"
        best={bestSide === "global"}
        savings={best?.savings_azn}
      >
        {glob.length === 0 ? (
          <p className="text-sm text-slate-500">Global fiyat kaydı yok.</p>
        ) : (
          <table className="w-full text-sm">
            <thead className="text-[11px] uppercase tracking-wider text-slate-500">
              <tr>
                <th className="pb-1 text-left font-medium">Mağaza</th>
                <th className="pb-1 text-right font-medium">Fiyat</th>
                <th className="pb-1 text-right font-medium">Kargo</th>
                <th className="pb-1 text-right font-medium">Gümrük</th>
                <th className="pb-1 text-right font-medium">Bakü Teslim</th>
              </tr>
            </thead>
            <tbody>
              {glob.map((o) => (
                <tr key={o.store} className="border-t border-white/[0.06]">
                  <td className="py-2">
                    <StoreLink store={o.store} url={o.url} />
                  </td>
                  <td className="py-2 text-right font-mono text-slate-300">{usd(o.price_usd)}</td>
                  <td className="py-2 text-right font-mono text-slate-300">{usd(o.shipping_usd)}</td>
                  <td className="py-2 text-right font-mono text-amber-300">{usd(o.duty_usd)}</td>
                  <td className="py-2 text-right font-mono font-semibold text-white">{azn(o.total_azn)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {settings && (
          <p className="mt-3 text-[11px] leading-relaxed text-slate-500">
            Baz = Fiyat + Ağırlık × Kargo/kg · Baz &gt; {usd(settings.duty_free_limit_usd)} ise Gümrük = (Baz −{" "}
            {usd(settings.duty_free_limit_usd)}) × {Math.round(Number(settings.duty_rate) * 100)}% +{" "}
            {usd(settings.declaration_fee_usd)} beyanname · Kur {Number(settings.usd_azn_rate).toFixed(2)} ₼/$
          </p>
        )}
      </Panel>
    </div>
  );
}
