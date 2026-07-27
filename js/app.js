/* app.js — view routing and event wiring */

const App = {
    banks: null,

    init() {
        this.wireEvents();
        this.renderExamCards();
        this.showView("select");
        this.refreshSelectResume();
    },

    /* --- exam selection --- */
    renderExamCards() {
        const grid = document.getElementById("exam-grid");
        grid.innerHTML = "";

        EXAMS.forEach((exam) => {
            const pct = passPercentFor(exam);

            const card = document.createElement("button");
            card.type = "button";
            card.className = "exam-card";
            card.setAttribute("aria-label", `Start ${exam.title}`);
            card.innerHTML =
                `<div class="exam-card-body">` +
                `<h3 class="exam-card-title">${escapeHtml(exam.title)}</h3>` +
                (exam.subtitle
                    ? `<p class="exam-card-subtitle">${escapeHtml(exam.subtitle)}</p>`
                    : "") +
                (exam.description
                    ? `<p class="exam-card-desc">${escapeHtml(exam.description)}</p>`
                    : "") +
                `</div>` +
                `<ul class="exam-card-facts">` +
                `<li><b>${exam.totalQuestions}</b> Questions</li>` +
                `<li><b>${exam.durationMinutes}</b> Minutes</li>` +
                `<li><b>${pct}%</b> To Pass</li>` +
                `</ul>` +
                `<span class="exam-card-cta">Select &rarr;</span>`;
            card.addEventListener("click", () => this.selectExam(exam.id));
            grid.appendChild(card);
        });
    },

    /** Show the resume banner on the select screen if a saved exam still exists. */
    refreshSelectResume() {
        const banner = document.getElementById("resume-banner-select");
        const saved = Storage.load();
        if (saved && !saved.finished && Date.now() < saved.endTime && getExam(saved.examId)) {
            document.getElementById("resume-title-select").textContent =
                getExam(saved.examId).title;
            banner.hidden = false;
        } else {
            if (saved && (saved.finished || Date.now() >= saved.endTime)) Storage.clear();
            banner.hidden = true;
        }
    },

    /** Enter the welcome screen for the chosen exam and load its banks. */
    async selectExam(examId) {
        try {
            setActiveExam(examId);
        } catch (err) {
            this.showSelectError(err.message);
            return;
        }

        this.updateFacts();
        this.showView("welcome");

        const startBtn = document.getElementById("btn-start");
        startBtn.disabled = true;
        try {
            this.banks = await loadBanks();
            startBtn.disabled = false;
        } catch (err) {
            this.showWelcomeError(err.message);
            return;
        }

        // Reflect the number of questions that will actually be drawn (the bank
        // may hold fewer than the exam's target count).
        const available = Object.values(this.banks).reduce((n, arr) => n + arr.length, 0);
        document.getElementById("fact-count").textContent =
            Math.min(CONFIG.TOTAL_QUESTIONS, available);

        // Offer to resume an in-progress exam that belongs to this exam.
        const saved = Storage.load();
        const banner = document.getElementById("resume-banner");
        if (saved && !saved.finished && saved.examId === examId && Date.now() < saved.endTime) {
            banner.hidden = false;
        } else {
            banner.hidden = true;
        }
    },

    updateFacts() {
        document.getElementById("welcome-title").textContent = CONFIG.EXAM_TITLE;
        if (ACTIVE_EXAM && ACTIVE_EXAM.description) {
            document.getElementById("welcome-desc").textContent = ACTIVE_EXAM.description;
        }
        document.getElementById("fact-count").textContent = CONFIG.TOTAL_QUESTIONS;
        document.getElementById("fact-minutes").textContent = CONFIG.DURATION_MINUTES;
        const pct = passPercentFor(ACTIVE_EXAM);
        document.getElementById("fact-pass").textContent = `${pct}%`;
        document.getElementById("q-total").textContent = CONFIG.TOTAL_QUESTIONS;
    },

    showWelcomeError(msg) {
        const el = document.getElementById("welcome-error");
        el.textContent = msg;
        el.hidden = false;
    },

    showSelectError(msg) {
        const el = document.getElementById("select-error");
        el.textContent = msg;
        el.hidden = false;
    },

    showView(name) {
        ["select", "welcome", "exam", "results"].forEach((v) => {
            document.getElementById(`view-${v}`).hidden = v !== name;
        });
        window.scrollTo(0, 0);
    },

    /** Return to the exam catalogue. */
    backToSelect() {
        document.getElementById("welcome-error").hidden = true;
        document.getElementById("select-error").hidden = true;
        this.refreshSelectResume();
        this.showView("select");
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

    /** Resume directly from the select screen (loads the saved exam's banks). */
    async resumeFromSelect() {
        const state = Storage.load();
        if (!state || state.finished || Date.now() >= state.endTime || !getExam(state.examId)) {
            Storage.clear();
            this.refreshSelectResume();
            return;
        }
        try {
            setActiveExam(state.examId);
            this.updateFacts();
            this.banks = await loadBanks();
        } catch (err) {
            this.showSelectError(err.message);
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
        document.getElementById("btn-back-to-select").addEventListener("click", () => this.backToSelect());
        document.getElementById("btn-resume-select").addEventListener("click", () => this.resumeFromSelect());
        document.getElementById("btn-discard-select").addEventListener("click", () => {
            Storage.clear();
            this.refreshSelectResume();
        });

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
