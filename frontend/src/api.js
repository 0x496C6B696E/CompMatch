import axios from "axios";

export const api = axios.create({ baseURL: "http://localhost:8000/api" });

export const getProfessions = () => api.get("/professions/").then((r) => r.data);
export const getPrograms = (professionId) =>
  api.get("/programs/", { params: { profession: professionId } }).then((r) => r.data);
export const postMatch = (programIds, deviceType) =>
  api.post("/match/", { program_ids: programIds, device_type: deviceType }).then((r) => r.data);

const aznFmt = new Intl.NumberFormat("az-AZ", { maximumFractionDigits: 0 });
const usdFmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
export const azn = (v) => (v == null ? "—" : `${aznFmt.format(Number(v))} ₼`);
export const usd = (v) => (v == null ? "—" : `$${usdFmt.format(Number(v))}`);
