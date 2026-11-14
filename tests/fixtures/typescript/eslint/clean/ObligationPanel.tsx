import { useState } from "react";

interface ObligationPanelProps {
  title: string;
  isOpen: boolean;
}

export function ObligationPanel({ title, isOpen }: ObligationPanelProps) {
  const [isExpanded, setExpanded] = useState(isOpen);
  return (
    <section aria-label={title}>
      <button type="button" onClick={() => setExpanded(!isExpanded)}>
        {title}
      </button>
    </section>
  );
}
