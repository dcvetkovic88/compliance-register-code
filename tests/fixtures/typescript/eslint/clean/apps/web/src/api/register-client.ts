// A generated client may call fetch: apps/web/src/api is the one place that calls a service (AR-W2).
export async function getObligations(): Promise<unknown> {
  const response = await fetch("/api/register/obligations");
  return (await response.json()) as unknown;
}
