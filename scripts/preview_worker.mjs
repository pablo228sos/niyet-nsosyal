import http from 'node:http';
import worker from '../dist/server/index.js';
const port = Number(process.env.DRSK_PREVIEW_PORT || 8767);
http.createServer(async (incoming, outgoing) => {
  try {
    const chunks = [];
    for await (const chunk of incoming) chunks.push(chunk);
    const body = Buffer.concat(chunks);
    const request = new Request(`http://127.0.0.1:${port}${incoming.url}`, {
      method: incoming.method, headers: incoming.headers,
      body: ['GET', 'HEAD'].includes(incoming.method) ? undefined : body,
    });
    const response = await worker.fetch(request);
    outgoing.writeHead(response.status, Object.fromEntries(response.headers));
    outgoing.end(Buffer.from(await response.arrayBuffer()));
  } catch (error) { outgoing.writeHead(500); outgoing.end('Preview error'); console.error(error); }
}).listen(port, '127.0.0.1', () => console.log(`DRSK production preview: http://127.0.0.1:${port}`));
