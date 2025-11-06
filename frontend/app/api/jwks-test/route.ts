import { NextResponse } from 'next/server';

export async function GET() {
  const publicUrl = process.env.NEXT_PUBLIC_KEYCLOAK_URL;
  const internal = process.env.KEYCLOAK_INTERNAL_URL || publicUrl;
  const realm = process.env.NEXT_PUBLIC_KEYCLOAK_REALM;
  const containerName = process.env.KEYCLOAK_CONTAINER_NAME;
  const candidates = [
    internal,
    internal?.replace('localhost','127.0.0.1'),
    publicUrl,
    publicUrl?.replace('localhost','127.0.0.1'),
    containerName ? `http://${containerName}:8081` : undefined,
  ].filter(Boolean) as string[];

  const results: any[] = [];
  for (const base of candidates) {
    const url = `${base.replace(/\/$/,'')}/realms/${realm}/protocol/openid-connect/certs`;
    const started = Date.now();
    try {
      const res = await fetch(url);
      const ms = Date.now() - started;
      if (!res.ok) {
        results.push({ host: base, url, ok: false, status: res.status, ms });
      } else {
        const data = await res.json();
        results.push({ host: base, url, ok: true, ms, count: (data.keys||[]).length });
        // stop early on success
        return NextResponse.json({ summary: 'success', tried: results });
      }
    } catch (e:any) {
      results.push({ host: base, url, ok: false, error: e.message });
    }
  }
  return NextResponse.json({ summary: 'all_failed', tried: results }, { status: 500 });
}
