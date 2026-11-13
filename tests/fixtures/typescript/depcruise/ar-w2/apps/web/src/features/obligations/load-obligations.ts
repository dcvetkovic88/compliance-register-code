import axios from "axios";

export const loadObligations = () => axios.get("/api/register/obligations");
