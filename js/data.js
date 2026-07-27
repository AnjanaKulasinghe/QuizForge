/* data.js — exam catalogue, active-exam configuration and question-bank loading */

/**
 * The exam catalogue. Each entry is a fully self-contained exam definition with
 * its own rule set: number of questions, duration, pass mark and question banks.
 * Add new exams here — everything else (selection page, rules, grading) adapts
 * automatically. All assets are bundled locally so the app runs fully offline.
 */
const EXAMS = Object.freeze([
    {
        id: "karate-referee",
        title: "Karate Referee Exam",
        subtitle: "WKF Kata & Kumite Rules",
        description:
            "Practice questions drawn from the WKF Kata and Kumite competition rulebooks.",
        totalQuestions: 30,
        durationMinutes: 30,
        passMark: 27,           // 90% of 30
        minPerDoc: 12,          // random per-document split bounds (2-bank exams)
        maxPerDoc: 19,          // effective range stays 12-18 so each doc has >=12
        banks: [
            { id: "kumite", file: "data/questions-kumite.json", pdf: "assets/kumite-rules.pdf" },
            { id: "kata", file: "data/questions-kata.json", pdf: "assets/kata-rules.pdf" }
        ]
    },
    {
        id: "comptia-security-plus",
        title: "CompTIA Security+ (SY0-701)",
        subtitle: "SY0-701 Practice Exam",
        description:
            "Original practice questions modelled on the CompTIA Security+ SY0-701 objectives, " +
            "with a detailed explanation for every answer option.",
        totalQuestions: 90,     // real exam is "up to 90"; the engine draws what the bank has
        durationMinutes: 90,
        passPercent: 83,        // 750 / 900 scaled score ≈ 83%
        banks: [
            { id: "securityplus", file: "data/questions-securityplus.json", pdf: "" }
        ]
    }
]);

/** Shared storage key. The saved state records which exam it belongs to. */
const STORAGE_KEY = "quizforge.exam.v1";

/**
 * The active exam's rule set. Populated by setActiveExam() before an exam is
 * built or rendered. The property names mirror the fields the rest of the app
 * reads (TOTAL_QUESTIONS, DURATION_MINUTES, PASS_MARK, BANKS, ...).
 */
const CONFIG = {
    STORAGE_KEY,
    EXAM_ID: null,
    EXAM_TITLE: null,
    TOTAL_QUESTIONS: 0,
    DURATION_MINUTES: 0,
    PASS_MARK: null,        // pass threshold expressed as a correct-answer count
    PASS_PERCENT: null,     // OR pass threshold expressed as a percentage
    MIN_PER_DOC: null,
    MAX_PER_DOC: null,
    BANKS: []
};

let ACTIVE_EXAM = null;

/** Look up an exam definition by id. */
function getExam(examId) {
    return EXAMS.find((e) => e.id === examId) || null;
}

/**
 * Make the given exam the active one, populating CONFIG with its rule set.
 * Returns the exam definition. Throws if the id is unknown.
 */
function setActiveExam(examId) {
    const exam = getExam(examId);
    if (!exam) throw new Error(`Unknown exam "${examId}".`);

    ACTIVE_EXAM = exam;
    CONFIG.EXAM_ID = exam.id;
    CONFIG.EXAM_TITLE = exam.title;
    CONFIG.TOTAL_QUESTIONS = exam.totalQuestions;
    CONFIG.DURATION_MINUTES = exam.durationMinutes;
    CONFIG.PASS_MARK = Number.isFinite(exam.passMark) ? exam.passMark : null;
    CONFIG.PASS_PERCENT = Number.isFinite(exam.passPercent) ? exam.passPercent : null;
    CONFIG.MIN_PER_DOC = Number.isFinite(exam.minPerDoc) ? exam.minPerDoc : null;
    CONFIG.MAX_PER_DOC = Number.isFinite(exam.maxPerDoc) ? exam.maxPerDoc : null;
    CONFIG.BANKS = exam.banks;
    return exam;
}

/**
 * Load all question banks for the active exam.
 * Returns { "<bankId>": [...], ... }.
 * Throws if a bank cannot be loaded (e.g. opened via file:// without a server).
 */
async function loadBanks() {
    if (!CONFIG.BANKS.length) {
        throw new Error("No exam selected.");
    }

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

/** The pass threshold as a whole-number percentage, for display purposes. */
function passPercentFor(exam) {
    if (exam && Number.isFinite(exam.passPercent)) return Math.round(exam.passPercent);
    if (exam && Number.isFinite(exam.passMark) && exam.totalQuestions) {
        return Math.round((exam.passMark / exam.totalQuestions) * 100);
    }
    return 0;
}
