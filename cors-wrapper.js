/**
 * CORS Wrapper for Python Worker
 * Adds proper CORS headers that Python Workers can't set
 * Uses Service Bindings for worker-to-worker communication
 */

const ALLOWED_ORIGINS = [
  'https://ny2026.foodikal.rs',
  'https://foodikal.rs'
];

function getCorsOrigin(requestOrigin) {
  if (requestOrigin && ALLOWED_ORIGINS.includes(requestOrigin)) {
    return requestOrigin;
  }
  return ALLOWED_ORIGINS[0];
}

function addCorsHeaders(response, origin) {
  const newHeaders = new Headers(response.headers);
  const corsOrigin = getCorsOrigin(origin);

  newHeaders.set('Access-Control-Allow-Origin', corsOrigin);
  newHeaders.set('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS');
  newHeaders.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  newHeaders.set('Access-Control-Max-Age', '86400');

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: newHeaders
  });
}

function handleOptions(origin) {
  const corsOrigin = getCorsOrigin(origin);

  return new Response(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': corsOrigin,
      'Access-Control-Allow-Methods': 'GET, POST, PUT, PATCH, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Max-Age': '86400'
    }
  });
}

export default {
  async fetch(request, env, ctx) {
    const origin = request.headers.get('Origin');

    // Handle OPTIONS preflight
    if (request.method === 'OPTIONS') {
      return handleOptions(origin);
    }

    // Proxy request to Python worker using Service Binding
    try {
      // Use service binding to call Python worker
      // The service binding handles the request directly without needing to construct a URL
      const response = await env.PYTHON_WORKER.fetch(request);

      // Add CORS headers to response
      return addCorsHeaders(response, origin);
    } catch (error) {
      console.error('Proxy error:', error);
      return new Response('Gateway Error: ' + error.message, { status: 502 });
    }
  }
};
