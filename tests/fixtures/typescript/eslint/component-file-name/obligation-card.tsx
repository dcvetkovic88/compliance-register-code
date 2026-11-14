interface ObligationCardProps {
  title: string;
}

export function ObligationCard({ title }: ObligationCardProps) {
  return <section aria-label={title}>{title}</section>;
}
