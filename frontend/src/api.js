import axios from "axios";

// Aynı origin: Django (8000) build edilmiş frontend'i servis eder; Vite dev'de (5173) proxy devreye girer.
export const api = axios.create({ baseURL: "/api" });

export const getProfessions = () => api.get("/professions/").then((r) => r.data);
export const getPrograms = (professionId) =>
  api.get("/programs/", { params: { profession: professionId } }).then((r) => r.data);
export const postMatch = (programIds, deviceType) =>
  api.post("/match/", { program_ids: programIds, device_type: deviceType }).then((r) => r.data);

const aznFmt = new Intl.NumberFormat("az-AZ", { maximumFractionDigits: 0 });
const usdFmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
export const azn = (v) => (v == null ? "—" : `${aznFmt.format(Number(v))} ₼`);
export const usd = (v) => (v == null ? "—" : `$${usdFmt.format(Number(v))}`);
