import { NextResponse } from 'next/server';

function getBackendUrl() {
  return (process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000')
    .replace('http://localhost:', 'http://127.0.0.1:');
}

export async function GET(request: Request) {
  try {
    const backendUrl = getBackendUrl();
    const query = request.url.split('?')[1] || '';
    const response = await fetch(`${backendUrl}/auth/status${query ? `?${query}` : ''}`, {
      method: 'GET',
      cache: 'no-store',
    });

    const payload = await response.json();
    return NextResponse.json(payload, { status: response.status });
  } catch (error) {
    console.error('Error fetching auth status:', error);
    return NextResponse.json(
      {
        status: 'error',
        connected: false,
        message: 'Failed to fetch auth status',
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}
