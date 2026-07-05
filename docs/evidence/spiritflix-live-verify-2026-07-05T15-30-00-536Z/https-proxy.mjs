
import http from "node:http";
import https from "node:https";
import { readFileSync } from "node:fs";
const key = readFileSync("/home/source/SpiritOS/certificates/spirit-dev-key.pem");
const cert = readFileSync("/home/source/SpiritOS/certificates/spirit-dev.pem");
const server = https.createServer({ key, cert }, (req, res) => {
  const proxy = http.request({
    hostname: "127.0.0.1",
    port: 3002,
    method: req.method,
    path: req.url,
    headers: { ...req.headers, host: "127.0.0.1:3000", "x-forwarded-proto": "https" },
  }, (upstream) => {
    res.writeHead(upstream.statusCode ?? 502, upstream.headers);
    upstream.pipe(res);
  });
  proxy.on("error", (error) => {
    res.writeHead(502, { "content-type": "text/plain" });
    res.end(String(error?.message ?? error));
  });
  req.pipe(proxy);
});
server.listen(3000, "0.0.0.0", () => console.log("SpiritFlix verify HTTPS proxy listening on :3000 -> :3002"));
