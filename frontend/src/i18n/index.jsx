import { createContext, useCallback, useContext, useMemo, useState } from "react";
import az from "./az.js";
import ru from "./ru.js";
import en from "./en.js";

export const LANGS = ["az", "ru", "en"];
const DICTS = { az, ru, en };
const KEY = "compmatch.lang";

function detect() {
  try {
    const saved = localStorage.getItem(KEY);
    if (LANGS.includes(saved)) return saved;
  } catch {}
  const nav = (navigator.language || "").slice(0, 2);
  return LANGS.includes(nav) ? nav : "az";
}

const Ctx = createContext(null);

export function LangProvider({ children }) {
  const [lang, setLangState] = useState(detect);
  const setLang = useCallback((l) => {
    setLangState(l);
    try { localStorage.setItem(KEY, l); } catch {}
    document.documentElement.lang = l;
  }, []);
  const value = useMemo(() => {
    const dict = DICTS[lang];
    // t("key", {n: 3}) -> "{n}" yer tutucularını doldurur; eksik anahtar AZ'ye düşer, o da yoksa anahtarı gösterir.
    const t = (key, vars) => {
      let s = dict[key] ?? az[key] ?? key;
      if (vars) for (const [k, v] of Object.entries(vars)) s = s.replaceAll(`{${k}}`, String(v));
      return s;
    };
    return { lang, setLang, t };
  }, [lang, setLang]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export const useLang = () => useContext(Ctx);
