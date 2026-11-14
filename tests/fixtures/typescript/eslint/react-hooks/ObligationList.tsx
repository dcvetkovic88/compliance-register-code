import { useState } from "react";

export function ObligationList({ isVisible }: { isVisible: boolean }) {
  if (!isVisible) {
    return null;
  }
  const [count] = useState(0);
  return <output>{count}</output>;
}
