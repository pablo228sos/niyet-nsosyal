const API_ORIGIN = 'https://niyet-nsosyal.vercel.app';
const HEADERS = {
  'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'no-referrer',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
};

const API_PATHS = new Set(['/api', '/api/experiment', '/api/human-help']);

export default {
  async fetch(request) {
    const url = new URL(request.url);

    if (API_PATHS.has(url.pathname)) {
      const experiment = url.pathname === '/api/experiment';
      const allowed = experiment ? request.method === 'GET' : ['GET', 'POST'].includes(request.method);
      if (!allowed) return new Response('Method not allowed', { status: 405 });

      let body;
      if (request.method === 'POST') {
        if (!request.headers.get('content-type')?.startsWith('application/json')) {
          return new Response('JSON required', { status: 415 });
        }
        if (Number(request.headers.get('content-length')) > 32768) {
          return new Response('Request too large', { status: 413 });
        }

        const reader = request.body?.getReader();
        let size = 0;
        const chunks = [];
        if (reader) {
          while (true) {
            const part = await reader.read();
            if (part.done) break;
            size += part.value.byteLength;
            if (size > 32768) {
              await reader.cancel();
              return new Response('Request too large', { status: 413 });
            }
            chunks.push(part.value);
          }
        }

        body = new Uint8Array(size);
        let offset = 0;
        for (const chunk of chunks) {
          body.set(chunk, offset);
          offset += chunk.byteLength;
        }
      }

      try {
        const upstream = await fetch(API_ORIGIN + url.pathname + url.search, {
          method: request.method,
          headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
          body,
          redirect: 'manual',
          signal: AbortSignal.timeout(20000),
        });

        // Never allow the proxy to hop to an unexpected host.
        if (upstream.status >= 300 && upstream.status < 400) {
          return Response.json(
            { error: 'backend_redirect' },
            { status: 502, headers: { ...HEADERS, 'Cache-Control': 'no-store' } },
          );
        }

        return new Response(upstream.body, {
          status: upstream.status,
          headers: {
            ...HEADERS,
            'Content-Type': 'application/json',
            'Cache-Control': 'no-store',
          },
        });
      } catch (error) {
        console.error(
          'API proxy unavailable',
          error instanceof Error ? error.message : 'Unknown fetch error',
        );
        return Response.json(
          { error: 'backend_unavailable' },
          { status: 503, headers: { ...HEADERS, 'Cache-Control': 'no-store' } },
        );
      }
    }

    if (!['GET', 'HEAD'].includes(request.method)) {
      return new Response('Method not allowed', { status: 405 });
    }

    const path =
      url.pathname === '/' || ['/live', '/live/'].includes(url.pathname)
        ? '/live.html'
        : ['/lab', '/lab/'].includes(url.pathname)
          ? '/lab.html'
          : url.pathname;

    const asset = ASSETS[path];
    if (!asset) {
      return new Response(
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Page not found · DRSK</title><main><h1>Page not found</h1><p>This page is not part of DRSK.</p><a href="/">Return to the feed</a></main></html>',
        { status: 404, headers: { ...HEADERS, 'Content-Type': 'text/html; charset=utf-8' } },
      );
    }

    const bytes = Uint8Array.from(
      atob(asset.body),
      (character) => character.charCodeAt(0),
    );
    return new Response(request.method === 'HEAD' ? null : bytes, {
      headers: {
        ...HEADERS,
        'Content-Type': asset.type,
        'Cache-Control': 'no-cache',
      },
    });
  },
};
