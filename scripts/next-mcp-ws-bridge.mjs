#!/usr/bin/env node
import { WebSocketServer } from "ws";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

process.env.NEXT_DEVTOOLS_HOST ||= "127.0.0.1";
process.env.NODE_TLS_REJECT_UNAUTHORIZED ||= "0";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(scriptDir, "..");
const nextDevtoolsDist = resolve(repoRoot, "node_modules", "next-devtools-mcp", "dist");
const { handler: nextjsCall } = await import(
  pathToFileURL(resolve(nextDevtoolsDist, "tools", "nextjs_call.js")).href
);
const { handler: nextjsIndex } = await import(
  pathToFileURL(resolve(nextDevtoolsDist, "tools", "nextjs_index.js")).href
);

const bridgePort = readIntEnv("NEXT_MCP_WS_PORT", 3901);
const nextPort = readIntEnv("NEXT_MCP_PORT", 3000);
const host = process.env.NEXT_MCP_WS_HOST || "127.0.0.1";

const bridgeTools = [
  {
    name: "get_errors",
    description: "Get current Next.js build, runtime, and type errors.",
    inputSchema: {
      type: "object",
      properties: {
        port: { type: "number", description: "Next.js dev server port." },
      },
      additionalProperties: true,
    },
  },
  {
    name: "get_page_metadata",
    description: "Query Next.js application routes, pages, and component metadata.",
    inputSchema: {
      type: "object",
      properties: {
        port: { type: "number", description: "Next.js dev server port." },
      },
      additionalProperties: true,
    },
  },
  {
    name: "nextjs_index",
    description: "Discover running Next.js dev servers and their MCP tools.",
    inputSchema: {
      type: "object",
      properties: {
        port: { type: "number", description: "Optional Next.js dev server port." },
      },
      additionalProperties: false,
    },
  },
];

const server = new WebSocketServer({ host, port: bridgePort });

server.on("connection", (socket) => {
  socket.on("message", async (rawMessage) => {
    let request;
    try {
      request = JSON.parse(rawMessage.toString("utf8"));
    } catch (error) {
      socket.send(JSON.stringify(jsonRpcError(null, -32700, "Parse error", error)));
      return;
    }

    try {
      const result = await handleJsonRpc(request);
      if (request.id !== undefined) {
        socket.send(JSON.stringify({ jsonrpc: "2.0", id: request.id, result }));
      }
    } catch (error) {
      socket.send(
        JSON.stringify(
          jsonRpcError(
            request.id ?? null,
            -32000,
            error instanceof Error ? error.message : String(error),
            error,
          ),
        ),
      );
    }
  });
});

server.on("listening", () => {
  console.log(
    `Next MCP WebSocket bridge listening on ws://${host}:${bridgePort} -> Next port ${nextPort}`,
  );
});

async function handleJsonRpc(request) {
  if (request.jsonrpc !== "2.0" || typeof request.method !== "string") {
    throw new Error("Invalid JSON-RPC request.");
  }

  if (request.method === "initialize") {
    return {
      protocolVersion: "2025-03-26",
      serverInfo: { name: "source-next-mcp-ws-bridge", version: "0.1.0" },
      capabilities: { tools: {} },
    };
  }

  if (request.method === "tools/list") {
    return { tools: bridgeTools };
  }

  if (request.method === "tools/call") {
    const name = request.params?.name;
    const args = request.params?.arguments || {};
    return callBridgeTool(name, args);
  }

  if (bridgeTools.some((tool) => tool.name === request.method)) {
    return callBridgeTool(request.method, request.params || {});
  }

  throw new Error(`Unsupported method: ${request.method}`);
}

async function callBridgeTool(toolName, args) {
  if (toolName === "nextjs_index") {
    return parseToolJson(await nextjsIndex(args));
  }

  if (toolName === "get_errors" || toolName === "get_page_metadata") {
    const port = args.port ?? nextPort;
    return parseToolJson(
      await nextjsCall({
        port,
        toolName,
        args: withoutBridgeOnlyArgs(args),
      }),
    );
  }

  throw new Error(`Unsupported tool: ${toolName}`);
}

function withoutBridgeOnlyArgs(args) {
  const nextArgs = { ...args };
  delete nextArgs.port;
  return nextArgs;
}

function parseToolJson(value) {
  if (typeof value !== "string") {
    return value;
  }
  try {
    return JSON.parse(value);
  } catch {
    return value;
  }
}

function jsonRpcError(id, code, message, error) {
  return {
    jsonrpc: "2.0",
    id,
    error: {
      code,
      message,
      data: error instanceof Error ? error.stack : String(error ?? ""),
    },
  };
}

function readIntEnv(name, defaultValue) {
  const rawValue = process.env[name];
  if (!rawValue) {
    return defaultValue;
  }

  const value = Number.parseInt(rawValue, 10);
  if (!Number.isFinite(value) || value <= 0) {
    throw new Error(`${name} must be a positive integer, got ${rawValue}.`);
  }
  return value;
}
