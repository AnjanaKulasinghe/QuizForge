/* data.js — exam configuration and question-bank loading */

const CONFIG = Object.freeze({
    TOTAL_QUESTIONS: 30,
    DURATION_MINUTES: 30,
    PASS_MARK: 27,            // 90% of 30
    MIN_PER_DOC: 12,          // random split bounds per document
    MAX_PER_DOC: 19,          // effective range stays 12-18 so each doc has >=12
    STORAGE_KEY: "quizforge.exam.v1",
    BANKS: [
        { id: "kumite", file: "data/questions-kumite.json", pdf: "assets/kumite-rules.pdf" },
        { id: "kata", file: "data/questions-kata.json", pdf: "assets/kata-rules.pdf" }
    ]
});

/**
 * Load all question banks.
 * Returns { "document-1": [...], "document-2": [...] }.
 * Throws if a bank cannot be loaded (e.g. opened via file:// without a server).
 */
async function loadBanks() {
    const banks = {};
    for (const bank of CONFIG.BANKS) {
        let res;
        try {
            res = await fetch(bank.file, { cache: "no-store" });
        } catch (err) {
            throw new Error(
                `Could not load "${bank.file}". If you opened index.html directly, ` +
                `run it through a local server (e.g. "python3 -m http.server").`
            );
        }
        if (!res.ok) {
            throw new Error(`Failed to load "${bank.file}" (HTTP ${res.status}).`);
        }
        const questions = await res.json();
        if (!Array.isArray(questions) || questions.length === 0) {
            throw new Error(`Bank "${bank.file}" is empty or invalid.`);
        }
        banks[bank.id] = questions;
    }
    return banks;
}

/** Map a documentId to its bundled PDF path. */
function pdfForDocument(documentId) {
    const bank = CONFIG.BANKS.find((b) => b.id === documentId);
    return bank ? bank.pdf : "";
}
