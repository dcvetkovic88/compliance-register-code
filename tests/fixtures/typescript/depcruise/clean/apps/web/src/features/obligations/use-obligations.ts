import { registerClient } from "../../api/register-client";

export function useObligations() {
  return registerClient.get("/obligations");
}
