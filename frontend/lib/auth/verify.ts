import { jwtVerify, createRemoteJWKSet } from 'jose';


const PUBLIC_URL = process.env.NEXT_PUBLIC_KEYCLOAK_URL || 'http://localhost:8082';
const INTERNAL_URL = process.env.KEYCLOAK_INTERNAL_URL || PUBLIC_URL;
const REALM = process.env.NEXT_PUBLIC_KEYCLOAK_REALM || 'bsw-realm';
const CLIENT_ID = process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID;
const ISSUER = `${PUBLIC_URL.replace(/\/$/, '')}/realms/${REALM}`;

const jwksFetchBase = INTERNAL_URL.replace(/\/$/, '');
const jwksUrl = `${jwksFetchBase}/realms/${REALM}/protocol/openid-connect/certs`;
const jwks = createRemoteJWKSet(new URL(jwksUrl));

let firstLog = true;
function logConfigOnce() {
  if (!firstLog) return;
  firstLog = false;
  console.log('[auth] verify config:', { PUBLIC_URL, INTERNAL_URL, jwksUrl, ISSUER, CLIENT_ID });
}

export async function verifyAccessToken(token: string) {
  try {
    logConfigOnce();
    const { payload } = await jwtVerify(token, jwks, { issuer: ISSUER });

    if (CLIENT_ID) {
      const aud: any = payload.aud;
      const azp: any = (payload as any).azp;
      const audOk = !aud
        || (Array.isArray(aud) ? aud.includes(CLIENT_ID) : aud === CLIENT_ID)
        || azp === CLIENT_ID;
      if (!audOk) {
        console.warn('[auth] Audience mismatch: aud=', aud, 'azp=', azp, 'expected=', CLIENT_ID);
      }
    }

    return payload;
  } catch (e: any) {
    console.error('[auth] Token verification failed:', e.message);
    throw e;
  }
}
