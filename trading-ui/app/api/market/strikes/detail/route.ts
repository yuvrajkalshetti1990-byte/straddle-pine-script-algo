import { NextRequest, NextResponse } from 'next/server';

function getBackendUrl() {
  return (process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000')
    .replace('http://localhost:', 'http://127.0.0.1:');
}

export async function GET(request: NextRequest) {
  try {
    const backendUrl = getBackendUrl();
    const query = request.nextUrl.searchParams.toString();
    const backendPath = `/api/v1/market/strikes/detail${query ? `?${query}` : ''}`;

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 60_000);

    const response = await fetch(`${backendUrl}${backendPath}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      signal: controller.signal,
      cache: 'no-store',
    });

    clearTimeout(timeout);

    const payload = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        {
          status: 'error',
          message: payload?.message || `Backend error: ${response.statusText}`,
          error: payload?.error || 'Failed to fetch strike detail',
        },
        { status: response.status }
      );
    }

    return NextResponse.json(payload);
  } catch (error) {
    console.error('Error fetching strike detail:', error);
    return NextResponse.json(
      {
        status: 'error',
        message: 'Failed to fetch strike detail',
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}
