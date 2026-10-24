import { Check } from "lucide-react";

export const STEPS = [
  "Meslek Seçimi",
  "Kullandığın Programlar",
  "Laptop / PC Seçimi",
  "Sistem Önerisi & Bakü/Global Maliyet",
];

export default function Stepper({ current }) {
  const pct = (current / (STEPS.length - 1)) * 100;
  return (
    <div className="glass rounded-2xl px-6 py-5">
      <div className="relative">
        {/* Ray + akışkan dolgu */}
        <div className="absolute left-5 right-5 top-5 h-1 rounded-full bg-white/[0.06]" />
        <div
          className="absolute left-5 top-5 h-1 rounded-full bg-gradient-to-r from-indigo-p via-purple-p to-cyan-p shadow-[0_0_14px_rgba(99,102,241,0.6)] transition-all duration-700 ease-out"
          style={{ width: `calc((100% - 2.5rem) * ${pct / 100})` }}
        />
        <ol className="relative grid grid-cols-4">
          {STEPS.map((label, i) => {
            const done = i < current;
            const active = i === current;
            return (
              <li key={label} className="flex flex-col items-center text-center gap-3">
                <span
                  className={[
                    "flex h-10 w-10 items-center justify-center rounded-full text-sm font-semibold transition-all duration-500",
                    done && "bg-indigo-p text-white shadow-[0_0_18px_rgba(99,102,241,0.5)]",
                    active && "bg-surface text-white ring-2 ring-indigo-500 shadow-[0_0_25px_rgba(99,102,241,0.35)] scale-110",
                    !done && !active && "bg-surface text-slate-500 border border-white/[0.08]",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                >
                  {done ? <Check size={18} /> : i + 1}
                </span>
                <span
                  className={`text-xs sm:text-sm font-medium leading-tight transition-colors duration-300 ${
                    active ? "text-white" : done ? "text-indigo-300" : "text-slate-500"
                  }`}
                >
                  {label}
                </span>
              </li>
            );
          })}
        </ol>
      </div>
    </div>
  );
}
