import { NextRequest, NextResponse } from 'next/server';

function getBackendUrl() {
  return (process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000')
    .replace('http://localhost:', 'http://127.0.0.1:');
}

export async function GET(request: NextRequest) {
  try {
    const backendUrl = getBackendUrl();
    const query = request.nextUrl.searchParams.toString();
    const response = await fetch(`${backendUrl}/auth/exchange${query ? `?${query}` : ''}`, {
      method: 'GET',
      cache: 'no-store',
    });

    const payload = await response.json();
    return NextResponse.json(payload, { status: response.status });
  } catch (error) {
    console.error('Error exchanging HDFC token:', error);
    return NextResponse.json(
      {
        status: 'error',
        message: 'Failed to exchange HDFC token',
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}
