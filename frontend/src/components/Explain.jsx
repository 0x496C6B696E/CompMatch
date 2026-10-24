import { useLang } from "../i18n/index.jsx";

/** Bilgisayardan anlamayanlar için: skorların ne anlama geldiği, açılır-kapanır (native <details>). */
export default function Explain() {
  const { t } = useLang();
  return (
    <details className="glass rounded-2xl px-5 py-3 text-sm">
      <summary className="cursor-pointer select-none font-medium text-snow">{t("explain.title")}</summary>
      <ul className="mt-3 space-y-2 text-mist">
        <li><span className="text-snow">CPU.</span> {t("explain.cpu")}</li>
        <li><span className="text-snow">GPU.</span> {t("explain.gpu")}</li>
        <li><span className="text-snow">RAM.</span> {t("explain.ram")}</li>
        <li><span className="text-snow">SSD.</span> {t("explain.ssd")}</li>
        <li>{t("explain.levels")}</li>
      </ul>
    </details>
  );
}
