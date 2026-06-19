# Human-Brain Architecture Contract

This is a recurrent whole-brain system. Verification can return control to Cartographer. Execution results return to the global workspace. Repair returns to verification. Final outcomes feed approved memory and future routing lessons.

Every subsystem row must carry: `brain_stage`, `brain_region`, `system_role`, `input_contract`, `output_contract`, `authority_contract`, `failure_contract`, `evidence_required`, `runtime_owner`, `required_task_classes`, and `downstream_consumers`.

0. Brainstem / Autonomic Substrate
1. Sensory Input
2. Thalamic Attention / Routing
3. Salience / Risk
4. Global Workspace
5. Hippocampal And Semantic Memory
6. Prefrontal Executive
7. Association-Cortex Specialists
8. Basal-Ganglia Policy / Action Selection
9. Motor Effectors
10. Cerebellar Verification And Repair
11. Reward And Consolidation

A subsystem counts as integrated only when the canonical live route invokes it, it receives real upstream state, performs its intended job, a downstream stage consumes its output, failure changes route or final result, invocation and consumption appear in one causal trace, a live test proves the behavior, and checkpoint/recovery survives where applicable.

Schemas, status pages, packets, previews, advisory output, mocks, dormant components, fixture success, and backend-substituted fallback output do not count.
