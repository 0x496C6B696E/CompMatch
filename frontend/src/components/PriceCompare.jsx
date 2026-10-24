import { ExternalLink } from "lucide-react";
import { azn, usd } from "../api.js";
import { useLang } from "../i18n/index.jsx";

const thresholdAzn = (settings) => Number(settings.duty_free_limit_usd) * Number(settings.usd_azn_rate);

function StoreName({ store, url, updatedAt }) {
  const title = updatedAt ? new Date(updatedAt).toLocaleDateString() : undefined;
  const safe = /^https?:\/\//i.test(url || ""); // admin/scraper'dan gelen link yalnızca http(s) ise tıklanır
  return safe ? (
    <a href={url} target="_blank" rel="noreferrer" title={title} className="inline-flex max-w-full items-center gap-1 text-snow hover:underline">
      <span className="truncate">{store}</span> <ExternalLink size={12} className="shrink-0 text-mist" />
    </a>
  ) : (
    <span className="truncate text-snow" title={title}>{store}</span>
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
        <span aria-hidden="true" className="absolute -inset-y-1 w-0 border-l border-dashed border-white/40" style={{ left: `${(threshold / max) * 100}%` }} />
      )}
    </div>
  );
}

function Badge({ savings }) {
  const { t } = useLang();
  const saved = savings != null && Number(savings) > 0;
  return (
    <span className="animate-badge-glow absolute -top-3 left-4 rounded-full bg-green-p px-3 py-1 text-xs font-semibold text-space">
      {saved ? t("price.badge.savings", { amount: azn(savings) }) : t("price.badge")}
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

function Row({ store, url, inStock, amount, updatedAt, children }) {
  const { t } = useLang();
  return (
    <div className="flex items-center gap-3">
      <span className="flex w-24 shrink-0 flex-col sm:w-28">
        <StoreName store={store} url={url} updatedAt={updatedAt} />
        {!inStock && <span className="text-xs text-mist">{t("price.outOfStock")}</span>}
      </span>
      {children}
      <span className={`num w-20 shrink-0 text-right font-display text-base font-semibold ${inStock ? "text-snow" : "text-mist"}`}>
        {azn(amount)}
      </span>
    </div>
  );
}

/** Çubukların nasıl okunacağı: sayfada bir kez, açılır-kapanır. */
export function CostLegend({ settings }) {
  const { t } = useLang();
  if (!settings) return null;
  return (
    <details className="glass rounded-2xl px-5 py-3 text-xs text-mist">
      <summary className="cursor-pointer select-none text-sm font-medium text-snow">{t("legend.title")}</summary>
      <p className="mt-3 flex flex-wrap gap-x-4 gap-y-1">
        <span className="inline-flex items-center gap-1.5"><i className="inline-block h-2 w-3 rounded-sm bg-cyan-p" /> {t("legend.local")}</span>
        <span className="inline-flex items-center gap-1.5"><i className="inline-block h-2 w-3 rounded-sm bg-purple-p" /> {t("legend.item")}</span>
        <span className="inline-flex items-center gap-1.5"><i className="inline-block h-2 w-3 rounded-sm bg-purple-p/50" /> {t("legend.ship")}</span>
        <span className="inline-flex items-center gap-1.5"><i className="seg-duty inline-block h-2 w-3 rounded-sm" /> {t("legend.duty")}</span>
        <span className="inline-flex items-center gap-1.5"><i className="inline-block h-3 w-px border-l border-dashed border-white/40" /> {t("legend.threshold", { amount: azn(thresholdAzn(settings)) })}</span>
      </p>
      <p className="num mt-2 max-w-[70ch]">
        {t("legend.formula", {
          perkg: usd(settings.shipping_per_kg_usd),
          limit: usd(settings.duty_free_limit_usd),
          rate: Math.round(Number(settings.duty_rate) * 100),
          fee: usd(settings.declaration_fee_usd),
          fx: Number(settings.usd_azn_rate).toLocaleString("tr-TR"),
        })}
      </p>
    </details>
  );
}

/** Bakü yerel mağazalar vs Global + Azerbaycan gümrük, yan yana Bento kartlar, ortak ₼ ölçeği. */
export default function PriceCompare({ prices, settings }) {
  const { t } = useLang();
  if (!prices) return null;
  const { local, global: glob, best } = prices;
  const max = Math.max(1, ...local.map((o) => Number(o.price_azn)), ...glob.map((o) => Number(o.total_azn)));
  const threshold = settings ? thresholdAzn(settings) : null;

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Panel title={t("price.local")} best={best?.side === "local"} savings={best?.savings_azn}>
        {local.length === 0 ? (
          <p className="mt-3 text-sm text-mist">{t("price.noLocal")}</p>
        ) : (
          <ul className="mt-4 space-y-3 text-sm">
            {local.map((o) => (
              <li key={o.store}>
                <Row store={o.store} url={o.url} inStock={o.in_stock} amount={o.price_azn} updatedAt={o.updated_at}>
                  <CostBar total={Number(o.price_azn)} max={max} dim={!o.in_stock} segments={[{ v: 1, cls: "bg-cyan-p" }]} />
                </Row>
              </li>
            ))}
          </ul>
        )}
      </Panel>

      <Panel title={t("price.global")} best={best?.side === "global"} savings={best?.savings_azn}>
        {glob.length === 0 ? (
          <p className="mt-3 text-sm text-mist">{t("price.noGlobal")}</p>
        ) : (
          <ul className="mt-4 space-y-3 text-sm">
            {glob.map((o) => (
              <li key={o.store}>
                <Row store={o.store} url={o.url} inStock={o.in_stock} amount={o.total_azn} updatedAt={o.updated_at}>
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
                  {Number(o.duty_usd) > 0
                    ? t("price.breakdown", { price: usd(o.price_usd), ship: usd(o.shipping_usd), duty: usd(o.duty_usd) })
                    : t("price.breakdown.free", { price: usd(o.price_usd), ship: usd(o.shipping_usd) })}
                </p>
              </li>
            ))}
          </ul>
        )}
      </Panel>
    </div>
  );
}
