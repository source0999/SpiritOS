# GLM-4-9B Preflight

generated_at: 2026-07-02T23:59:46Z

## git status --short
 M source_proxy/api/decision.py
 M source_proxy/tasks/long_running.py
 M source_proxy/tests/test_coding_regression_pack.py
 M source_proxy/tests/test_long_running_tasks.py
 M src/app/v1/actions/execute-approved/route.ts
 M src/app/v1/coding/agent-lab-sweep/route.ts
 M src/app/v1/decisions/prompt-packet/route.ts
 M src/components/coding/CodingCockpitShell.tsx
 M src/components/coding/__tests__/coding-cockpit-shell.test.tsx
 M src/lib/coding/__tests__/agent-lab-baseline-server.test.ts
 M src/lib/coding/__tests__/dummy-coder-10-grader.test.ts
 M src/lib/coding/__tests__/reversible-trial-runner.test.ts
 M src/lib/coding/agent-lab-baseline-server.ts
 M src/lib/coding/agent-lab-cleanup.ts
 M src/lib/coding/dummy-coder-10-grader.ts
 M src/lib/coding/reversible-trial-runner.ts
 M tests/ui-agent-trials/fixtures/dummy-product-site/index.html
 M tests/ui-agent-trials/fixtures/dummy-product-site/package.json
 M tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js
 M tests/ui-agent-trials/fixtures/dummy-product-site/src/styles.css
?? docs/evidence/glm4-9b-model-lanes-20260702-195946/
?? docs/source-proxy-design-studio-implementation-pivot-20260701/DEPRECATED.md
?? docs/source-proxy-design-studio-real-integration-pivot-20260702/
?? scripts/media/spiritflix_library_smart_rescan_status.json
?? scripts/media/spiritflix_smart_rescan_rollback_20260702T0240.json
?? src/app/api/spiritflix/library-smart-rescan/

## git branch
bench/glm4-9b-model-lanes

## ollama list
NAME                                                                  ID              SIZE      MODIFIED     
hf.co/yuxinlu1/gemma-4-12B-coder-fable5-composer2.5-v1-GGUF:Q4_K_M    5434f64afb3f    7.4 GB    2 days ago      
qwen2.5-coder:14b                                                     9ec8897f747e    9.0 GB    2 days ago      
hf.co/deepreinforce-ai/Ornith-1.0-9B-GGUF:Q4_K_M                      0e5b9bbae3c6    5.6 GB    3 days ago      
gemma3n:e4b                                                           15cb39fd9394    7.5 GB    3 weeks ago     
hermes4:latest                                                        3e79497c9643    9.0 GB    4 weeks ago     
hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:Q4_K_M                 ce5cb56a7898    9.0 GB    4 weeks ago     
hermes3:8b-abliterated                                                621eb9c2e65e    4.7 GB    5 weeks ago     
mannix/llama3-8b-ablitered-v3:latest                                  46688a22037e    4.7 GB    5 weeks ago     
qwen2.5-coder:7b                                                      dae161e27b0e    4.7 GB    6 weeks ago     
llama3.1:8b                                                           46e0c10c039e    4.9 GB    6 weeks ago     
llama3:latest                                                         365c0bd3c000    4.7 GB    2 months ago    

## nvidia-smi
Thu Jul  2 19:59:46 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 580.159.03             Driver Version: 580.159.03     CUDA Version: 13.0     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 3060        Off |   00000000:01:00.0 Off |                  N/A |
|  0%   42C    P8             16W /  170W |    5153MiB /  12288MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|    0   N/A  N/A            1749      G   /usr/lib/xorg/Xorg                       16MiB |
|    0   N/A  N/A         1197113      C   /usr/local/bin/ollama                  5118MiB |
+-----------------------------------------------------------------------------------------+

## free -h
               total        used        free      shared  buff/cache   available
Mem:            15Gi       7.3Gi       281Mi       207Mi       8.5Gi       8.2Gi
Swap:          4.0Gi       4.0Gi        88Ki

## df -h
Filesystem      Size  Used Avail Use% Mounted on
/dev/sdb2       457G  368G   67G  85% /
/dev/sda1       7.3T  388G  6.5T   6% /mnt/spirit-8tb

## ollama storage
/mnt/spirit-8tb/ollama-models
54G	/mnt/spirit-8tb/ollama-models/models/
