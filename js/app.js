/* app.js — view routing and event wiring */

const App = {
    banks: null,

    async init() {
        this.wireEvents();
        this.updateFacts();
        this.showView("welcome");

        try {
            this.banks = await loadBanks();
        } catch (err) {
            this.showWelcomeError(err.message);
            document.getElementById("btn-start").disabled = true;
            return;
        }

        // Offer to resume an in-progress exam.
        const saved = Storage.load();
        if (saved && !saved.finished && Date.now() < saved.endTime) {
            document.getElementById("resume-banner").hidden = false;
        } else if (saved) {
            Storage.clear();
        }
    },

    updateFacts() {
        document.getElementById("fact-count").textContent = CONFIG.TOTAL_QUESTIONS;
        document.getElementById("fact-minutes").textContent = CONFIG.DURATION_MINUTES;
        const pct = Math.round((CONFIG.PASS_MARK / CONFIG.TOTAL_QUESTIONS) * 100);
        document.getElementById("fact-pass").textContent = `${pct}%`;
        document.getElementById("q-total").textContent = CONFIG.TOTAL_QUESTIONS;
    },

    showWelcomeError(msg) {
        const el = document.getElementById("welcome-error");
        el.textContent = msg;
        el.hidden = false;
    },

    showView(name) {
        ["welcome", "exam", "results"].forEach((v) => {
            document.getElementById(`view-${v}`).hidden = v !== name;
        });
        window.scrollTo(0, 0);
    },

    /* --- exam lifecycle --- */
    startNewExam() {
        Storage.clear();
        const state = buildExam(this.banks);
        Storage.save(state);
        this.enterExam(state);
    },

    resumeExam() {
        const state = Storage.load();
        if (!state || state.finished || Date.now() >= state.endTime) {
            Storage.clear();
            document.getElementById("resume-banner").hidden = true;
            return;
        }
        this.enterExam(state);
    },

    enterExam(state) {
        this.showView("exam");
        Exam.init(state, { onTimeUp: () => this.finishExam(true) });
    },

    finishExam(auto = false) {
        if (!auto) {
            const missing = Exam.unansweredCount();
            const total = Exam.state.questions.length;
            if (missing > 0) {
                const ok = window.confirm(
                    `You have answered ${total - missing} of ${total} questions. ` +
                    `Submit the exam now?`
                );
                if (!ok) return;
            }
        }

        Exam.stopTimer();
        Exam.state.finished = true;
        const result = Grading.grade(Exam.state);
        Grading.render(result);
        Storage.clear();
        this.showView("results");
    },

    restart() {
        Storage.clear();
        document.getElementById("resume-banner").hidden = true;
        this.showView("welcome");
    },

    /* --- events --- */
    wireEvents() {
        document.getElementById("btn-start").addEventListener("click", () => this.startNewExam());
        document.getElementById("btn-resume").addEventListener("click", () => this.resumeExam());
        document.getElementById("btn-discard").addEventListener("click", () => {
            Storage.clear();
            document.getElementById("resume-banner").hidden = true;
        });

        document.getElementById("btn-back").addEventListener("click", () => Exam.back());
        document.getElementById("btn-next").addEventListener("click", () => {
            if (Exam.isLast()) this.finishExam(false);
            else Exam.next();
        });
        document.getElementById("btn-finish-side").addEventListener("click", () => this.finishExam(false));

        document.getElementById("btn-print").addEventListener("click", () => window.print());
        document.getElementById("btn-restart").addEventListener("click", () => this.restart());
    }
};

document.addEventListener("DOMContentLoaded", () => App.init());
