import { NextResponse } from 'next/server';

function getBackendUrl() {
  return (process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000')
    .replace('http://localhost:', 'http://127.0.0.1:');
}

export async function GET() {
  try {
    const backendUrl = getBackendUrl();
    
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 30_000);

    const response = await fetch(`${backendUrl}/api/v1/market/nifty-price`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      signal: controller.signal,
    });
    clearTimeout(timeout);

    if (!response.ok) {
      throw new Error(`Backend error: ${response.statusText}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching NIFTY price:', error);
    return NextResponse.json(
      { 
        status: 'error', 
        message: 'Failed to fetch NIFTY price',
        error: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}
