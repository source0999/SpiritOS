# Increment 1.2 - Hermes 4 runtime smoke

Date: 2026-05-29T19:52:37-04:00

```text
Thinking...
Okay, the user wants me to reply exactly with "HERMES4_ALIAS_OK". Let me ma[2D[K
make sure I understand the instruction correctly. They specified to reply e[1D[K
exactly that phrase, so I need to output it without any extra text or modif[5D[K
modifications. 

I should check if there are any hidden requirements or if this is a test to[2D[K
to ensure I follow instructions precisely. Since the user mentioned preserv[7D[K
preserving safety boundaries, I'll confirm that the response doesn't includ[6D[K
include any unsafe content. The phrase "HERMES4_ALIAS_OK" seems to be a sta[3D[K
status or confirmation message, so it's likely safe.

No need to add explanations or additional information. Just a straightforwa[13D[K
straightforward reply. Let me double-check the spelling and capitalization [K
to match exactly. Yes, it's all caps with underscores. Alright, ready to se[2D[K
send the exact response.
...done thinking.

HERMES4_ALIAS_OK

{
    "models": [
        {
            "name": "hermes4:latest",
            "model": "hermes4:latest",
            "modified_at": "2026-05-29T19:47:02.020002088-04:00",
            "size": 9001755837,
            "digest": "3e79497c964380ab2cf68708d4b1dce602484aa3989bc5d2322630efc6e731a7",
            "details": {
                "parent_model": "",
                "format": "gguf",
                "family": "qwen3",
                "families": [
                    "qwen3"
                ],
                "parameter_size": "14.8B",
                "quantization_level": "Q4_K_M"
            }
        },
        {
            "name": "hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:Q4_K_M",
            "model": "hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:Q4_K_M",
            "modified_at": "2026-05-29T19:45:49.353447581-04:00",
            "size": 9001755690,
            "digest": "ce5cb56a789801c7b6c575b313d5f3779a4d208c742c2f8f3fd43393e90d92a5",
            "details": {
                "parent_model": "",
                "format": "gguf",
                "family": "qwen3",
                "families": [
                    "qwen3"
                ],
                "parameter_size": "14.8B",
                "quantization_level": "unknown"
            }
        },
        {
            "name": "hermes3:8b-abliterated",
            "model": "hermes3:8b-abliterated",
            "modified_at": "2026-05-24T22:02:47.182678608-04:00",
            "size": 4675905733,
            "digest": "621eb9c2e65e986b4ab002c354e4da35d7041a746dcec0bbcb67b5f2c70e1f3f",
            "details": {
                "parent_model": "",
                "format": "gguf",
                "family": "llama",
                "families": [
                    "llama"
                ],
                "parameter_size": "8.0B",
                "quantization_level": "Q4_0"
            }
        },
        {
            "name": "mannix/llama3-8b-ablitered-v3:latest",
            "model": "mannix/llama3-8b-ablitered-v3:latest",
            "modified_at": "2026-05-24T22:02:36.820607791-04:00",
            "size": 4675905733,
            "digest": "46688a22037ee2799d368c0c0497c38f53d596a10fd3a201089f7e6ea8477301",
            "details": {
                "parent_model": "",
                "format": "gguf",
                "family": "llama",
                "families": [
                    "llama"
                ],
                "parameter_size": "8.0B",
                "quantization_level": "Q4_0"
            }
        },
        {
            "name": "qwen2.5-coder:7b",
            "model": "qwen2.5-coder:7b",
            "modified_at": "2026-05-17T21:36:01.722215506-04:00",
            "size": 4683087561,
            "digest": "dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364",
            "details": {
                "parent_model": "",
                "format": "gguf",
                "family": "qwen2",
                "families": [
                    "qwen2"
                ],
                "parameter_size": "7.6B",
                "quantization_level": "Q4_K_M"
            }
        },
        {
            "name": "llama3.1:8b",
            "model": "llama3.1:8b",
            "modified_at": "2026-05-17T21:25:37.251728579-04:00",
            "size": 4920753328,
            "digest": "46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e",
            "details": {
                "parent_model": "",
                "format": "gguf",
                "family": "llama",
                "families": [
                    "llama"
                ],
                "parameter_size": "8.0B",
                "quantization_level": "Q4_K_M"
            }
        },
        {
            "name": "llama3:latest",
            "model": "llama3:latest",
            "modified_at": "2026-04-16T23:00:59.305368764-04:00",
            "size": 4661224676,
            "digest": "365c0bd3c000a25d28ddbf732fe1c6add414de7275464c4e4d1c3b5fcb5d8ad1",
            "details": {
                "parent_model": "",
                "format": "gguf",
                "family": "llama",
                "families": [
                    "llama"
                ],
                "parameter_size": "8.0B",
                "quantization_level": "Q4_0"
            }
```

## Result

GO.

- `ollama run hermes4 "Reply exactly: HERMES4_ALIAS_OK"` returned `HERMES4_ALIAS_OK`.
- The base HF model invocation was started but did not complete promptly with the requested marker; the foreground `ollama run` client was terminated after the long-running check. This did not stop the Ollama service.
- The base model is visible through `http://localhost:11434/api/tags` as `hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:Q4_K_M`, with matching 14.8B GGUF details.
- `git diff --check` passed after the increment.
