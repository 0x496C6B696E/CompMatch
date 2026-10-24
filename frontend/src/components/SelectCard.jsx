import { Check } from "lucide-react";
import Icon from "./Icon.jsx";

const TONES = {
  indigo: "bg-indigo-p/15 text-indigo-300",
  cyan: "bg-cyan-p/15 text-cyan-300",
  purple: "bg-purple-p/15 text-purple-300",
};

/** Ponytale Bento seçim kartı: hover'da yükselir, seçildiğinde neon ring. */
export default function SelectCard({ icon, title, subtitle, selected, onClick, tone = "indigo", className = "", children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      className={[
        "group relative flex w-full flex-col text-left glass rounded-2xl p-5 transition-all duration-300",
        "hover:-translate-y-1 hover:bg-white/[0.05] hover:border-white/[0.14]",
        selected ? "ring-2 ring-indigo-500 shadow-[0_0_25px_rgba(99,102,241,0.35)] bg-indigo-500/[0.06]" : "",
        className,
      ].join(" ")}
    >
      <div className="flex w-full items-start gap-4">
        <span className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${TONES[tone]}`}>
          <Icon name={icon} size={22} strokeWidth={1.75} />
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="font-display text-xl font-semibold leading-tight text-snow">{title}</h3>
          {subtitle && <p className="mt-1 text-sm leading-snug text-mist">{subtitle}</p>}
        </div>
        <span
          aria-hidden="true"
          className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full transition-all duration-200 ${
            selected ? "bg-indigo-p text-white" : "border border-white/[0.12] text-transparent"
          }`}
        >
          <Check size={14} strokeWidth={3} />
        </span>
      </div>
      {children}
    </button>
  );
}
