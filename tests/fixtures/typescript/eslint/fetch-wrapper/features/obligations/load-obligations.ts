import { getJson } from "../../http";

export function loadObligations(): Promise<unknown> {
  return getJson("/api/register/obligations");
}
