import { useEffect, useState } from "react";
import { LANGS, LangProvider, useLang } from "./i18n/index.jsx";
import Wizard from "./pages/Wizard.jsx";
import Laptops from "./pages/Laptops.jsx";
import Parts from "./pages/Parts.jsx";

/** Hash tabanlı yönlendirme: #/ sihirbaz, #/laptops, #/pc. Kütüphane yok. */
function useRoute() {
  const read = () => (location.hash.startsWith("#/laptops") ? "laptops" : location.hash.startsWith("#/pc") ? "pc" : "wizard");
  const [route, setRoute] = useState(read);
  useEffect(() => {
    const on = () => setRoute(read());
    addEventListener("hashchange", on);
    return () => removeEventListener("hashchange", on);
  }, []);
  return route;
}

const NAV = [
  ["wizard", "#/", "nav.wizard"],
  ["laptops", "#/laptops", "nav.laptops"],
  ["pc", "#/pc", "nav.pc"],
];

function Shell() {
  const { lang, setLang, t } = useLang();
  const route = useRoute();

  return (
    <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
      <header className="mb-6 flex flex-wrap items-center gap-x-6 gap-y-4">
        <a href="#/" className="mr-auto min-w-0">
          <h1 className="font-display text-2xl font-bold leading-none tracking-[-0.02em] text-snow">CompMatch</h1>
          <p className="mt-1.5 text-sm text-mist">{t("app.tagline")}</p>
        </a>
        <nav aria-label="Main" className="order-last -mx-4 flex w-[calc(100%+2rem)] gap-1 overflow-x-auto px-4 sm:order-none sm:mx-0 sm:w-auto sm:px-0">
          {NAV.map(([key, href, label]) => (
            <a
              key={key}
              href={href}
              aria-current={route === key ? "page" : undefined}
              className={`shrink-0 rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                route === key ? "bg-white/[0.08] text-snow" : "text-mist hover:text-snow"
              }`}
            >
              {t(label)}
            </a>
          ))}
        </nav>
        <div role="group" aria-label="Language" className="glass flex shrink-0 rounded-full p-1">
          {LANGS.map((l) => (
            <button
              key={l}
              type="button"
              onClick={() => setLang(l)}
              aria-pressed={lang === l}
              className={`rounded-full px-3 py-1 text-xs font-semibold uppercase transition-colors ${
                lang === l ? "bg-indigo-p text-white" : "text-mist hover:text-snow"
              }`}
            >
              {l}
            </button>
          ))}
        </div>
      </header>

      {route === "wizard" && <Wizard />}
      {route === "laptops" && <Laptops />}
      {route === "pc" && <Parts />}
    </main>
  );
}

export default function App() {
  return (
    <LangProvider>
      <Shell />
    </LangProvider>
  );
}
