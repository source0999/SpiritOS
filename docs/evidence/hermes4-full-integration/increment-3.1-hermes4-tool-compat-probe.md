# Increment 3.1 - Hermes 4 tool compatibility probe

Date: 2026-05-29T19:57:58-04:00

```text
=== simple OpenAI-compatible chat probe ===
{
    "id": "chatcmpl-702",
    "object": "chat.completion",
    "created": 1780099143,
    "model": "hermes4",
    "system_fingerprint": "fp_ollama",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "HERMES4_OPENAI_COMPAT_OK",
                "reasoning": "Okay, the user wants me to reply exactly with the string \"HERMES4_OPENAI_COMPAT_OK\". Let me make sure I understand the request correctly. They provided a specific phrase to output without any modifications. There's no additional context or follow-up questions mentioned here. \n\nI should just echo back that exact string. It's a straightforward instruction to avoid any interpretation. My response needs to be precise. No extra spaces, punctuation, or variations. Just the exact text as given. \n\nNo need to engage in conversation beyond that. I'll confirm the reply is accurate. Let me double-check: \"HERMES4_OPENAI_COMPAT_OK\" \u2013 that's 20 characters, starts with H and ends with K. All uppercase. Seems correct. \n\nAlright, ready to respond.\n"
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 58,
        "completion_tokens": 168,
        "total_tokens": 226
    }
}
=== tool schema probe shape, non-mutating ===
STATUS 200
{"id":"chatcmpl-241","object":"chat.completion","created":1780099150,"model":"hermes4","system_fingerprint":"fp_ollama","choices":[{"index":0,"message":{"role":"assistant","content":"","reasoning":"Okay, so the user is saying not to call any tools and to reply exactly with \"HERMES4_TOOL_SCHEMA_ACCEPTED_OR_DECLINED\". Let me make sure I understand the instruction.\n\nFirst, the user wants a specific response. The message is pretty straightforward, so I don't need to use any functions or tools here. I just have to output that exact string. But wait, maybe I should think about any hidden parts? Like, is there a chance they want me to confirm I received the message? But the instruction says to reply exactly as specified. So no extra words, just the string.\n\nAlso, the user mentioned \"HERMES4_TOOL_SCHEMA_ACCEPTED_OR_DECLINED\" which seems to be a specific string. I need to check if there's any formatting required. The example shows it's a single line. So I'll just output that exact line without any markdown or additional text. Got it. No commas, no quotes, just the string as is. Alright, that's all. Just return the exact response without doing anything else.\n","tool_calls":[{"id":"call_fdbjd9at","index":0,"type":"function","function":{"name":"noop_status","arguments":"{}"}}]},"finish_reason":"tool_calls"}],"usage":{"prompt_tokens":174,"completion_tokens":234,"total_tokens":408}}

```

## Result

GO with caution.

- OpenAI-compatible `/v1/chat/completions` worked for `model=hermes4` and returned `HERMES4_OPENAI_COMPAT_OK`.
- Hermes 4 accepted the OpenAI-compatible `tools` schema with HTTP 200.
- The tool-schema response emitted a `tool_calls` entry for `noop_status` even though the prompt said not to call tools. Treat this as schema compatibility, not as safe autonomous tool-use behavior.
- Do not enable file edit/dev command tools by default from this result.
