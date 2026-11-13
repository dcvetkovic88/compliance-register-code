import { ShellPage } from "../../../../../packages/shell/src/ShellPage";
import { useObligations } from "./use-obligations";

export function ObligationPage() {
  useObligations();
  return <ShellPage />;
}
