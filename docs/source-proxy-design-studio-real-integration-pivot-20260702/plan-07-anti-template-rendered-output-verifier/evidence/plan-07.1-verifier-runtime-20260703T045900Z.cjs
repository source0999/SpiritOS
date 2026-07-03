"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.verifyRenderedAntiTemplate = verifyRenderedAntiTemplate;
const motifAnchors = [
    "spiritos",
    "source proxy",
    "coding cockpit",
    "design studio",
    "design workbench",
    "design sandbox",
    "coding agent",
    "visual review",
    "design demo",
];
function renderedCorpus(input) {
    return `${input.rendered_text ?? ""}\n${input.dom_snapshot ?? ""}`.toLowerCase();
}
function hasRenderedEvidence(input) {
    return Boolean(input.rendered_text?.trim() || input.dom_snapshot?.trim() || input.screenshot_metadata);
}
function addSignal(signals, id, evidence) {
    signals.push({ id, evidence });
}
function verifyRenderedAntiTemplate(input) {
    if (!hasRenderedEvidence(input)) {
        return {
            anti_template_verdict: "REJECT_TEXT_ONLY_INPUT",
            project_motif_rendered_evidence: [],
            reject_or_repair_reason: "rendered_dom_or_screenshot_metadata_required",
            template_signal_count: 0,
            template_signal_matches: [],
        };
    }
    const corpus = renderedCorpus(input);
    const screenshot = input.screenshot_metadata ?? {};
    const signals = [];
    if (screenshot.dominant_layout === "centered_hero" || /\b(start building|ask anything|ship faster)\b/.test(corpus)) {
        addSignal(signals, "centered_hero_block", "hero-like first viewport language or metadata detected");
    }
    if ((screenshot.color_families ?? []).some((color) => /purple|blue|violet|indigo/.test(color))) {
        addSignal(signals, "purple_blue_gradient", "purple/blue color family metadata detected");
    }
    const visibleCards = screenshot.visible_card_count ?? 0;
    const glassCards = screenshot.glass_card_count ?? 0;
    if (visibleCards > 0 && glassCards / visibleCards > 0.5) {
        addSignal(signals, "generic_glass_cards", "more than half of visible cards are glass cards");
    }
    if (/\b(features|feature one|feature two|feature three)\b/.test(corpus) && visibleCards >= 3) {
        addSignal(signals, "three_card_feature_grid", "generic feature grid language with at least three cards");
    }
    if ((screenshot.pricing_card_count ?? 0) > 0 || /\b(pricing|pro plan|enterprise plan)\b/.test(corpus)) {
        addSignal(signals, "pricing_tiers", "pricing tier language or card metadata detected");
    }
    if (/\b(privacy|terms|contact)\b/.test(corpus) && /\b(footer|all rights reserved)\b/.test(corpus)) {
        addSignal(signals, "bland_footer", "generic footer language detected");
    }
    if (/\b(blob|orb|aura|bokeh)\b/.test(corpus)) {
        addSignal(signals, "decorative_blobs", "decorative blob/orb language detected");
    }
    if (screenshot.dominant_layout === "hero_left_cards_right") {
        addSignal(signals, "hero_left_cards_right", "default hero-left/cards-right layout metadata detected");
    }
    if (screenshot.dominant_layout === "glass_sidebar_canvas_fab") {
        addSignal(signals, "glass_sidebar_canvas_fab", "default glass sidebar/canvas/FAB layout metadata detected");
    }
    const motifEvidence = motifAnchors.filter((anchor) => corpus.includes(anchor));
    const hasMotif = motifEvidence.length > 0;
    const templateSignalCount = signals.length;
    const verdict = templateSignalCount >= 4
        ? "GENERIC_TEMPLATE_REJECT"
        : templateSignalCount >= 2 && !hasMotif
            ? "GENERIC_TEMPLATE_REPAIR_REQUIRED"
            : "GENERIC_TEMPLATE_PASS";
    return {
        anti_template_verdict: verdict,
        project_motif_rendered_evidence: motifEvidence,
        reject_or_repair_reason: verdict === "GENERIC_TEMPLATE_PASS"
            ? "rendered_output_has_project_specific_motif_or_low_template_signal_count"
            : "rendered_output_matches_generic_template_signals",
        template_signal_count: templateSignalCount,
        template_signal_matches: signals,
    };
}
