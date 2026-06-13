# Final Proof Summary

Verdict: NO-GO
Behavior result: 5/10 PASS, 5 FAIL, threshold 8/10 behavior PASS

Failed prompts:
- final-l3-clean-02 `make a parking garage cost sharer`: route_blocked_no_preview
- final-l3-clean-03 `make a dusk dawn palette switch`: route_blocked_no_preview
- final-l3-clean-05 `make a pretend balcony forecast tile`: weather_static_when_update_expected
- final-l3-clean-09 `make a secret phrase strength gauge`: route_blocked_no_preview
- final-l3-clean-10 `make a finger paint doodle pad`: drawing_canvas_no_pixel_change

Grade recommendation: Do not accept Level 3 as GO yet. The fresh similar wording did not generalize to the 8/10 threshold.

Model lane: Qwen local coder invoked. Gemma/Hermes verifier lanes were preview-only and not invoked.
