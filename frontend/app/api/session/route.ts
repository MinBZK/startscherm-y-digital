import { NextRequest, NextResponse } from 'next/server';
import { verifyAccessToken } from '@/lib/auth/verify';

export async function POST(req: NextRequest) {
  try {
    const { token } = await req.json();
    if (!token) return NextResponse.json({ error: 'token missing' }, { status: 400 });

    // Verify before setting cookie
    try {
      await verifyAccessToken(token);
    } catch (e: any) {
      return NextResponse.json({ error: 'verification_failed', detail: e.message }, { status: 401 });
    }

    return new NextResponse(null, {
      status: 204,
      headers: {
        'Set-Cookie': `bsw_access=${token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=900`,
      },
    });
  } catch (e: any) {
    return NextResponse.json({ error: 'session_endpoint_error', detail: e.message }, { status: 500 });
  }
}

export async function DELETE() {
  return new NextResponse(null, {
    status: 204,
    headers: {
      'Set-Cookie': 'bsw_access=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0',
    },
  });
}
