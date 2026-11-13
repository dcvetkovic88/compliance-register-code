import { Dialog } from "@radix-ui/react-dialog";
import { Menu } from "lucide-react";
import { Header } from "./header";

export function ShellPage() {
  return <Dialog><Menu /><Header /></Dialog>;
}
