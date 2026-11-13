export function classify(months: number): string {
  if (months === 1) return "one";
  if (months === 2) return "two";
  if (months === 3) return "three";
  if (months === 4) return "four";
  if (months === 5) return "five";
  if (months === 6) return "six";
  if (months === 7) return "seven";
  if (months === 8) return "eight";
  if (months === 9) return "nine";
  if (months === 10) return "ten";
  return "many";
}
