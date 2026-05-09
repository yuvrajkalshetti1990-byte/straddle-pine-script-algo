import { NextResponse } from 'next/server';

function getBackendUrl() {
  return (process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000')
    .replace('http://localhost:', 'http://127.0.0.1:');
}

export async function GET() {
  try {
    const backendUrl = getBackendUrl();
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10_000);
    const response = await fetch(`${backendUrl}/api/v1/market/strikes/translate/self-test`, {
      signal: controller.signal,
      cache: 'no-store',
    });
    clearTimeout(timeout);
    const payload = await response.json();
    return NextResponse.json(payload);
  } catch {
    return NextResponse.json({ status: 'error', message: 'self-test unavailable' }, { status: 500 });
  }
}
