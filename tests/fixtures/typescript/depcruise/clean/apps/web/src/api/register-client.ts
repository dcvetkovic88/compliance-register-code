import axios from "axios";

export const registerClient = axios.create({ baseURL: "/api/register" });
