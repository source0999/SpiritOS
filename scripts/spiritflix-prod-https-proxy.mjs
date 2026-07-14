#!/usr/bin/env node
import { createServer } from "node:https";
import { request } from "node:http";
import { readFileSync } from "node:fs";

const args = new Map();
for (let index = 2; index < process.argv.length; index += 2) {
  args.set(process.argv[index], process.argv[index + 1]);
}

const port = Number(args.get("--port") ?? process.env.SPIRITFLIX_PROD_PORT ?? "3000");
const targetPort = Number(args.get("--target-port") ?? process.env.SPIRITFLIX_PROD_INTERNAL_PORT ?? "3002");
const keyPath = args.get("--key") ?? "./certificates/spirit-dev-key.pem";
const certPath = args.get("--cert") ?? "./certificates/spirit-dev.pem";

if (!Number.isInteger(port) || port <= 0) throw new Error(`Invalid public port: ${port}`);
if (!Number.isInteger(targetPort) || targetPort <= 0) throw new Error(`Invalid target port: ${targetPort}`);

const server = createServer(
  {
    key: readFileSync(keyPath),
    cert: readFileSync(certPath),
  },
  (clientRequest, clientResponse) => {
    // Keep the browser-visible host intact for upstream same-origin checks;
    // the connection target remains the loopback host configured below.
    const headers = { ...clientRequest.headers, host: clientRequest.headers.host ?? `127.0.0.1:${targetPort}` };
    const upstream = request(
      {
        hostname: "127.0.0.1",
        port: targetPort,
        method: clientRequest.method,
        path: clientRequest.url,
        headers,
      },
      (upstreamResponse) => {
        clientResponse.writeHead(upstreamResponse.statusCode ?? 502, upstreamResponse.headers);
        upstreamResponse.pipe(clientResponse);
      },
    );

    upstream.on("error", (error) => {
      if (clientResponse.headersSent) {
        clientResponse.destroy(error);
        return;
      }
      clientResponse.writeHead(502, { "content-type": "text/plain; charset=utf-8" });
      clientResponse.end("SpiritFlix production upstream is unavailable.");
    });

    clientRequest.pipe(upstream);
  },
);

server.listen(port, "0.0.0.0", () => {
  console.log(`SpiritFlix HTTPS proxy listening on 0.0.0.0:${port} -> http://127.0.0.1:${targetPort}`);
});
