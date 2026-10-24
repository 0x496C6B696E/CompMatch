import PriceCompare from "./PriceCompare.jsx";

const TIER_TONE = { value: "text-cyan-300", recommended: "text-indigo-300", pro: "text-purple-300" };

function Spec({ label, value, sub }) {
  return (
    <div className="rounded-xl bg-white/[0.03] px-3 py-2">
      <div className="text-xs text-mist">{label}</div>
      <div className="text-sm leading-snug text-snow">{value}</div>
      {sub && <div className="num text-xs text-mist">{sub}</div>}
    </div>
  );
}

export default function LaptopResults({ laptops, settings }) {
  if (!laptops?.length) {
    return (
      <p className="glass rounded-2xl p-6 text-mist">
        Bu gereksinimleri karşılayan laptop yok. Admin panelinden laptop ekleyebilir veya daha az program seçebilirsin.
      </p>
    );
  }
  return (
    <ol className="space-y-6">
      {laptops.map(({ tier, label, laptop, meets, prices }, i) => (
        <li key={laptop.id} className="glass rounded-2xl p-5 sm:p-6">
          <header className="flex flex-wrap items-start justify-between gap-x-6 gap-y-3">
            <div className="min-w-0">
              <p className={`text-sm font-medium ${TIER_TONE[tier]}`}>
                {i + 1}. {label}
              </p>
              <h3 className="font-display text-2xl font-semibold leading-tight text-snow sm:text-3xl">{laptop.name}</h3>
              <p className="mt-1 text-sm text-mist">
                {laptop.brand}, {laptop.screen}, {Number(laptop.weight_kg).toLocaleString("tr-TR")} kg
              </p>
            </div>
            <span
              className={`shrink-0 rounded-full px-3 py-1 text-xs font-medium ${
                meets === "rec" ? "bg-green-p/15 text-green-p" : "bg-cyan-p/15 text-cyan-300"
              }`}
            >
              {meets === "rec" ? "Önerilen gereksinimi karşılıyor" : "Minimum gereksinimi karşılıyor"}
            </span>
          </header>

          <div className="mt-5 grid grid-cols-2 gap-2 lg:grid-cols-4">
            <Spec label="İşlemci" value={laptop.cpu} sub={`skor ${laptop.cpu_score.toLocaleString("tr-TR")}`} />
            <Spec label="Ekran kartı" value={laptop.gpu} sub={`skor ${laptop.gpu_score.toLocaleString("tr-TR")}`} />
            <Spec label="RAM" value={`${laptop.ram_gb} GB`} />
            <Spec label="SSD" value={`${laptop.ssd_gb} GB`} />
          </div>

          <div className="mt-6">
            <PriceCompare prices={prices} settings={settings} />
          </div>
        </li>
      ))}
    </ol>
  );
}
