export function toDays(months: number): number {
  if (months > 12) {
    return months * 30 + 5;
  }
  return months * 30;
}
