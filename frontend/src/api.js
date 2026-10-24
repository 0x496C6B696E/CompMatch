import axios from "axios";

// Aynı origin: Django (8000) build edilmiş frontend'i servis eder; Vite dev'de (5173) proxy devreye girer.
export const api = axios.create({ baseURL: "/api" });
const get = (url, params) => api.get(url, { params }).then((r) => r.data);

export const getProfessions = (lang) => get("/professions/", { lang });
export const getPrograms = (professionId, lang) => get("/programs/", { profession: professionId, lang });
export const getLaptops = (lang) => get("/laptops/", { lang });
export const getComponents = (lang) => get("/components/", { lang });
export const getSettings = () => get("/settings/");
export const postMatch = (programIds, deviceType, lang) =>
  api.post("/match/", { program_ids: programIds, device_type: deviceType }, { params: { lang } }).then((r) => r.data);

// Sayfadaki tüm sayılar aynı ayırıcıyı kullansın: 1.470 ₼, 784 $, 14.000
const fmt = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 0 });
export const num = (v) => fmt.format(Number(v));
export const azn = (v) => (v == null ? "—" : `${fmt.format(Number(v))} ₼`);
export const usd = (v) => (v == null ? "—" : `${fmt.format(Number(v))} $`);
