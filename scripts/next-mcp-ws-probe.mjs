#!/usr/bin/env node
import WebSocket from "ws";

const toolName = process.argv[2] || "get_errors";
const bridgeUrl = process.env.NEXT_MCP_WS_URL || "ws://127.0.0.1:3901";
const nextPort = process.env.NEXT_MCP_PORT
  ? Number.parseInt(process.env.NEXT_MCP_PORT, 10)
  : undefined;

const socket = new WebSocket(bridgeUrl);

socket.on("open", () => {
  socket.send(
    JSON.stringify({
      jsonrpc: "2.0",
      id: 1,
      method: "tools/call",
      params: {
        name: toolName,
        arguments: nextPort ? { port: nextPort } : {},
      },
    }),
  );
});

socket.on("message", (data) => {
  console.log(data.toString("utf8"));
  socket.close();
});

socket.on("error", (error) => {
  console.error(error.message);
  process.exitCode = 1;
});
