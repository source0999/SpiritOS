# Increment 4.1 - Spirit frontend health

Date: 2026-05-29T20:00:01-04:00

```text
{
    "ok": true,
    "service": "ollama",
    "model": "llama3.1:8b",
    "baseURL": "http://127.0.0.1:11434/v1",
    "status": "online",
    "diagnostics": {
        "engine": "Ollama",
        "maxOutputTokens": 1024,
        "maxOutputTokensSource": "default (1024)",
        "oracleMaxOutputTokens": 1024,
        "oracleMaxOutputTokensSource": "inherits SPIRIT_MAX_OUTPUT_TOKENS (ORACLE_MAX_OUTPUT_TOKENS unset)",
        "chatModel": "llama3.1:8b",
        "oracleLaneModel": "llama3.1:8b",
        "context": {
            "label": "8192",
            "source": "OLLAMA_NUM_CTX"
        },
        "tts": {
            "provider": "ElevenLabs",
            "voice": "sIak7pFapfSLCfctxdOu",
            "source": "TTS_PROVIDER=elevenlabs"
        },
        "stt": {
            "provider": "Whisper (Faster-Whisper)",
            "url": "localhost:8000",
            "source": "default (http://localhost:8000)",
            "transcribePath": "/v1/audio/transcriptions"
        }
    }
}
    "ok": true,
    "service": "ollama",
    "model": "llama3.1:8b",
        "engine": "Ollama",
        "maxOutputTokens": 1024,
        "maxOutputTokensSource": "default (1024)",
        "oracleMaxOutputTokens": 1024,
        "oracleMaxOutputTokensSource": "inherits SPIRIT_MAX_OUTPUT_TOKENS (ORACLE_MAX_OUTPUT_TOKENS unset)",
        "chatModel": "llama3.1:8b",
        "oracleLaneModel": "llama3.1:8b",
            "source": "OLLAMA_NUM_CTX"
```

## Result

GO for route availability, runtime default mismatch recorded.

- `https://localhost:3000/api/spirit/health` responded with `ok: true`.
- Live SpiritOS frontend health reports `model: llama3.1:8b` and `chatModel: llama3.1:8b`, not Hermes 4.
- Because real `.env.local` must not be read or printed, this gate does not inspect the live secret-bearing env file.
- Operator fix required for live frontend default: set the frontend runtime `OLLAMA_MODEL=hermes4` (and optionally `ORACLE_OLLAMA_MODEL=hermes3:8b-abliterated`) in the live environment, then restart only the Next dev server when approved.
