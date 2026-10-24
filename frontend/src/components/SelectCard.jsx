import { Check } from "lucide-react";
import Icon from "./Icon.jsx";

/** Ponytale Bento seçim kartı: hover'da yükselir, seçildiğinde neon ring. */
export default function SelectCard({ icon, title, subtitle, selected, onClick, accent = "indigo", children }) {
  const accentBg = {
    indigo: "from-indigo-p/30 to-purple-p/20 text-indigo-300",
    cyan: "from-cyan-p/30 to-indigo-p/20 text-cyan-300",
    purple: "from-purple-p/30 to-indigo-p/20 text-purple-300",
  }[accent];

  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      className={[
        "group relative w-full text-left glass rounded-2xl p-5 transition-all duration-300",
        "hover:-translate-y-1 hover:bg-white/[0.05] hover:border-white/[0.14]",
        selected
          ? "ring-2 ring-indigo-500 shadow-[0_0_25px_rgba(99,102,241,0.35)] bg-indigo-500/[0.06]"
          : "",
      ].join(" ")}
    >
      <div className="flex items-start gap-4">
        <span
          className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${accentBg} transition-transform duration-300 group-hover:scale-110`}
        >
          <Icon name={icon} size={22} />
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="font-semibold text-white leading-snug">{title}</h3>
          {subtitle && <p className="mt-1 text-sm text-slate-400 leading-snug">{subtitle}</p>}
          {children}
        </div>
        <span
          className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full border transition-all duration-300 ${
            selected
              ? "border-indigo-400 bg-indigo-p text-white scale-100"
              : "border-white/[0.12] text-transparent scale-90"
          }`}
        >
          <Check size={14} />
        </span>
      </div>
    </button>
  );
}
