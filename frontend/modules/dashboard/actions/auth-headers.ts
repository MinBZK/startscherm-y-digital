"use server";

import { cookies } from "next/headers";

export async function buildAuthHeaders(
  extra?: Record<string, string>,
  options?: { cookieName?: string }
): Promise<HeadersInit> {
  const hdrs: Record<string, string> = { ...(extra || {}) };
  const name = options?.cookieName || "bsw_access";
  try {
    const c = await cookies();
    const token = c.get(name)?.value;
    if (token) {
      hdrs["Authorization"] = `Bearer ${token}`;
    }
  } catch {
    // Ignore cookie access errors.
  }
  return hdrs;
}
