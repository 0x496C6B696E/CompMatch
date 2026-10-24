import { ExternalLink } from "lucide-react";
import { azn, usd } from "../api.js";

const thresholdAzn = (settings) => Number(settings.duty_free_limit_usd) * Number(settings.usd_azn_rate);

function StoreName({ store, url }) {
  return url ? (
    <a href={url} target="_blank" rel="noreferrer" className="inline-flex max-w-full items-center gap-1 text-snow hover:underline">
      <span className="truncate">{store}</span> <ExternalLink size={12} className="shrink-0 text-mist" />
    </a>
  ) : (
    <span className="truncate text-snow">{store}</span>
  );
}

/** Aynı ₼ ölçeğinde çubuk; parçalar (ürün / kargo / gümrük) orantılı. */
function CostBar({ total, max, segments, dim, threshold }) {
  return (
    <div className={`relative h-3 flex-1 rounded-sm bg-white/[0.05] ${dim ? "opacity-35" : ""}`}>
      <div className="bar-grow flex h-full overflow-hidden rounded-sm" style={{ width: `${(total / max) * 100}%` }}>
        {segments.map((s, i) => (
          <span key={i} className={s.cls} style={{ flex: `${s.v} 0 0` }} />
        ))}
      </div>
      {threshold != null && threshold < max && (
        <span
          aria-hidden="true"
          className="absolute -inset-y-1 w-0 border-l border-dashed border-white/40"
          style={{ left: `${(threshold / max) * 100}%` }}
        />
      )}
    </div>
  );
}

function Badge({ savings }) {
  const saved = savings != null && Number(savings) > 0;
  return (
    <span className="animate-badge-glow absolute -top-3 left-4 rounded-full bg-green-p px-3 py-1 text-xs font-semibold text-space">
      En Karlı Seçenek{saved ? ` (${azn(savings)} Tasarruf)` : ""}
    </span>
  );
}

function Panel({ title, best, savings, children }) {
  return (
    <div className={`relative glass rounded-2xl p-4 pt-5 sm:p-5 sm:pt-6 ${best ? "ring-1 ring-green-p/60 bg-green-p/[0.04]" : ""}`}>
      {best && <Badge savings={savings} />}
      <h4 className="font-display text-lg font-semibold text-snow">{title}</h4>
      {children}
    </div>
  );
}

function Row({ store, url, inStock, amount, children }) {
  return (
    <div className="flex items-center gap-3">
      <span className="flex w-24 shrink-0 flex-col sm:w-28">
        <StoreName store={store} url={url} />
        {!inStock && <span className="text-xs text-mist">stok yok</span>}
      </span>
      {children}
      <span className={`num w-20 shrink-0 text-right font-display text-base font-semibold ${inStock ? "text-snow" : "text-mist"}`}>
        {azn(amount)}
      </span>
    </div>
  );
}

/** Çubukların nasıl okunacağı: sayfada bir kez gösterilir. */
export function CostLegend({ settings }) {
  if (!settings) return null;
  const ratePct = Math.round(Number(settings.duty_rate) * 100);
  return (
    <div className="space-y-1.5 text-xs text-mist">
      <p className="flex flex-wrap gap-x-4 gap-y-1">
        <span className="inline-flex items-center gap-1.5"><i className="inline-block h-2 w-3 rounded-sm bg-cyan-p" /> Bakü fiyatı</span>
        <span className="inline-flex items-center gap-1.5"><i className="inline-block h-2 w-3 rounded-sm bg-purple-p" /> ürün</span>
        <span className="inline-flex items-center gap-1.5"><i className="inline-block h-2 w-3 rounded-sm bg-purple-p/50" /> kargo</span>
        <span className="inline-flex items-center gap-1.5"><i className="seg-duty inline-block h-2 w-3 rounded-sm" /> gümrük</span>
        <span className="inline-flex items-center gap-1.5"><i className="inline-block h-3 w-px border-l border-dashed border-white/40" /> {azn(thresholdAzn(settings))} gümrüksüz sınır</span>
      </p>
      <p className="num max-w-[70ch]">
        Baz = fiyat + ağırlık × {usd(settings.shipping_per_kg_usd)}/kg. Baz {usd(settings.duty_free_limit_usd)} üstüyse gümrük
        %{ratePct} + {usd(settings.declaration_fee_usd)} beyanname. Kur {Number(settings.usd_azn_rate).toLocaleString("tr-TR")} ₼/$.
        Her üründe iki panel aynı ölçeği paylaşır.
      </p>
    </div>
  );
}

/** Bakü yerel mağazalar vs Global + Azerbaycan gümrük, yan yana Bento kartlar, ortak ₼ ölçeği. */
export default function PriceCompare({ prices, settings }) {
  if (!prices) return null;
  const { local, global: glob, best } = prices;
  const max = Math.max(1, ...local.map((o) => Number(o.price_azn)), ...glob.map((o) => Number(o.total_azn)));
  const threshold = settings ? thresholdAzn(settings) : null;

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Panel title="Bakü'de" best={best?.side === "local"} savings={best?.savings_azn}>
        {local.length === 0 ? (
          <p className="mt-3 text-sm text-mist">Bu ürün için Bakü fiyatı girilmemiş. Admin panelinden ekleyebilirsin.</p>
        ) : (
          <ul className="mt-4 space-y-3 text-sm">
            {local.map((o) => (
              <li key={o.store}>
                <Row store={o.store} url={o.url} inStock={o.in_stock} amount={o.price_azn}>
                  <CostBar total={Number(o.price_azn)} max={max} dim={!o.in_stock} segments={[{ v: 1, cls: "bg-cyan-p" }]} />
                </Row>
              </li>
            ))}
          </ul>
        )}
      </Panel>

      <Panel title="Global'den getirilirse" best={best?.side === "global"} savings={best?.savings_azn}>
        {glob.length === 0 ? (
          <p className="mt-3 text-sm text-mist">Bu ürün için global fiyat girilmemiş. Admin panelinden ekleyebilirsin.</p>
        ) : (
          <ul className="mt-4 space-y-3 text-sm">
            {glob.map((o) => (
              <li key={o.store}>
                <Row store={o.store} url={o.url} inStock={o.in_stock} amount={o.total_azn}>
                  <CostBar
                    total={Number(o.total_azn)}
                    max={max}
                    dim={!o.in_stock}
                    threshold={threshold}
                    segments={[
                      { v: Number(o.price_usd), cls: "bg-purple-p" },
                      { v: Number(o.shipping_usd), cls: "bg-purple-p/50" },
                      { v: Number(o.duty_usd), cls: "seg-duty" },
                    ]}
                  />
                </Row>
                <p className="num ml-27 mt-1 text-xs text-mist sm:ml-31">
                  {usd(o.price_usd)} ürün, {usd(o.shipping_usd)} kargo
                  {Number(o.duty_usd) > 0 ? `, ${usd(o.duty_usd)} gümrük` : ", gümrüksüz"}
                </p>
              </li>
            ))}
          </ul>
        )}
      </Panel>
    </div>
  );
}
