interface ShellTitleProps {
  title: string;
}

export function ShellTitle({ title }: ShellTitleProps) {
  return <h1>{title}</h1>;
}
