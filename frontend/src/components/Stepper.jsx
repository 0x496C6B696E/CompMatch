export const STEPS = [
  "Meslek Seçimi",
  "Kullandığın Programlar",
  "Laptop / PC Seçimi",
  "Sistem Önerisi & Bakü/Global Maliyet Analizi",
];

/** Dört parçalı ray: geçilen adımlar dolu, aktif adım parlıyor, sıradakiler boş. */
export default function Stepper({ current }) {
  return (
    <nav aria-label="Adımlar" className="glass rounded-2xl px-5 py-4 sm:px-6">
      <ol className="grid grid-cols-4 gap-2 sm:gap-3">
        {STEPS.map((label, i) => {
          const done = i < current;
          const active = i === current;
          return (
            <li key={label} aria-current={active ? "step" : undefined}>
              <div className="h-1 overflow-hidden rounded-full bg-white/[0.07]">
                <div
                  className={[
                    "h-full rounded-full transition-[width] duration-700 ease-out",
                    active
                      ? "bg-linear-to-r from-indigo-p to-cyan-p shadow-[0_0_14px_rgba(99,102,241,0.7)]"
                      : "bg-indigo-p",
                  ].join(" ")}
                  style={{ width: done || active ? "100%" : "0%" }}
                />
              </div>
              <div className="mt-3 flex items-baseline gap-2">
                <span
                  className={`font-display text-lg font-semibold leading-none ${
                    active ? "text-snow" : done ? "text-indigo-300" : "text-mist/60"
                  }`}
                >
                  {i + 1}
                </span>
                <span
                  className={`hidden text-sm leading-snug sm:block ${
                    active ? "text-snow" : done ? "text-mist" : "text-mist/60"
                  }`}
                >
                  {label}
                </span>
              </div>
            </li>
          );
        })}
      </ol>
      <p className="mt-2 text-sm text-snow sm:hidden">{STEPS[current]}</p>
    </nav>
  );
}
