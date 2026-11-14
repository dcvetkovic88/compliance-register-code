import { Header } from "../../layout/Header";
import { LocaleSwitch } from "../../layout/LocaleSwitch";
import { Navigation } from "../../layout/Navigation";
import { ThemeToggle } from "../../layout/ThemeToggle";

export function ObligationLayout() {
  return (
    <>
      <Header />
      <Navigation />
      <LocaleSwitch />
      <ThemeToggle />
    </>
  );
}
