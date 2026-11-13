import { registerClient } from "../../api/register-client";

export function ObligationCount() {
  void registerClient.get("/obligations");
  return <output />;
}
