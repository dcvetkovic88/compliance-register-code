import { registerClient } from "../../../apps/web/src/api/register-client";

export function TranslatedTitle() {
  void registerClient.get("/titles");
  return <output />;
}
