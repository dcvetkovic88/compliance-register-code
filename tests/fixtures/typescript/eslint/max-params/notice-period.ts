export function toDays(years: number, months: number, weeks: number, days: number, hours: number): number {
  return years * 365 + months * 30 + weeks * 7 + days + hours / 24;
}
