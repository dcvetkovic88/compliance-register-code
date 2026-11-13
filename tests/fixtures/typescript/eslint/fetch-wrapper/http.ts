// A local wrapper around fetch outside apps/web/src/api: a feature that imports it bypasses the generated client.
export async function getJson(path: string): Promise<unknown> {
  const response = await fetch(path);
  return (await response.json()) as unknown;
}
