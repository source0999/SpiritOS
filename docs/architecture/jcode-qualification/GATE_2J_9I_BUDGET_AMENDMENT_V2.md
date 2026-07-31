# Gate 2-J.9I Evidence-Derived Budget Amendment V2

The unchanged task's fake preflight produced a canonical 4,791-byte request
with the exact effective Qwen 14B model, three exposed tools, and no unexpected
model reference. An exact compatible tokenizer was not locally available, so
the conservative approved method is `ceil(bytes / 2)`: 2,396 tokens.

With a 256-token protocol reserve and 25 percent headroom, the calculated
requirement is 3,315 tokens. The smallest approved tier is therefore 4,096
input tokens. Output is fixed at 1,024; real-model requests are capped at two.
The original task manifest remains unchanged.
