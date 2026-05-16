#!/usr/bin/env node
import { spawn } from "node:child_process";
import { createServer } from "node:http";
import WebSocket from "ws";

const sentinel = "TS2322: Type 'string' is not assignable to type 'number'.";
const mockNextServer = createServer((request, response) => {
  if (request.method !== "POST" || request.url !== "/_next/mcp") {
    response.writeHead(404).end();
    return;
  }

  let body = "";
  request.on("data", (chunk) => {
    body += chunk;
  });
  request.on("end", () => {
    const payload = JSON.parse(body);
    response.writeHead(200, { "content-type": "text/event-stream" });
    response.end(
      `data: ${JSON.stringify({
        jsonrpc: "2.0",
        id: payload.id,
        result: {
          content: [{ type: "text", text: sentinel }],
          isError: false,
        },
      })}\n\n`,
    );
  });
});

mockNextServer.listen(0, "127.0.0.1", async () => {
  const mockNextPort = mockNextServer.address().port;
  const bridgePort = await pickPort();
  const bridge = spawn(
    process.execPath,
    ["./scripts/next-mcp-ws-bridge.mjs"],
    {
      env: {
        ...process.env,
        NEXT_MCP_PORT: String(mockNextPort),
        NEXT_MCP_WS_PORT: String(bridgePort),
      },
      stdio: ["ignore", "pipe", "pipe"],
    },
  );

  let bridgeOutput = "";
  bridge.stdout.on("data", (chunk) => {
    bridgeOutput += chunk.toString("utf8");
    if (bridgeOutput.includes("listening")) {
      runProbe(bridgePort, bridge, mockNextServer).catch((error) => {
        console.error(error);
        cleanup(bridge, mockNextServer, 1);
      });
    }
  });
  bridge.stderr.pipe(process.stderr);
});

async function runProbe(bridgePort, bridge, server) {
  const response = await callWebSocket(bridgePort);
  const text = JSON.stringify(response);
  if (!text.includes(sentinel)) {
    throw new Error(`Smoke response did not include sentinel. Response: ${text}`);
  }

  console.log(text);
  cleanup(bridge, server, 0);
}

function callWebSocket(port) {
  return new Promise((resolve, reject) => {
    const socket = new WebSocket(`ws://127.0.0.1:${port}`);
    socket.on("open", () => {
      socket.send(
        JSON.stringify({
          jsonrpc: "2.0",
          id: 1,
          method: "tools/call",
          params: { name: "get_errors", arguments: {} },
        }),
      );
    });
    socket.on("message", (data) => {
      resolve(JSON.parse(data.toString("utf8")));
      socket.close();
    });
    socket.on("error", reject);
  });
}

function pickPort() {
  return new Promise((resolve) => {
    const server = createServer();
    server.listen(0, "127.0.0.1", () => {
      const port = server.address().port;
      server.close(() => resolve(port));
    });
  });
}

function cleanup(bridge, server, exitCode) {
  bridge.kill();
  server.close(() => {
    process.exit(exitCode);
  });
}
