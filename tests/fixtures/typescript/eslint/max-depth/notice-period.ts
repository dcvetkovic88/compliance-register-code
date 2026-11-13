export function countLong(periods: number[][]): number {
  let count = 0;
  for (const months of periods) {
    for (const month of months) {
      if (month > 12) {
        if (month > 24) {
          count += 1;
        }
      }
    }
  }
  return count;
}
