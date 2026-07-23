/* exam.js — exam construction, rendering, navigation and timer */

/* ---- pure helpers ---- */

function shuffle(arr) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
}

function sample(arr, n) {
    return shuffle(arr).slice(0, n);
}

/** Choose how many questions come from doc 1 vs doc 2 (sums to TOTAL). */
function pickSplit(total, min, max, availA, availB) {
    const lo = Math.max(min, total - max, total - availB);
    const hi = Math.min(max, total - min, availA);
    if (lo > hi) {
        // Not enough questions to honour the min/max split — fall back to a
        // best-effort split that still sums to total.
        const a = Math.min(availA, Math.max(0, total - Math.min(availB, total)));
        return [a, total - a];
    }
    const a = lo + Math.floor(Math.random() * (hi - lo + 1));
    return [a, total - a];
}

/** Build a fresh exam from loaded banks. Returns a persistable state object. */
function buildExam(banks) {
    const ids = CONFIG.BANKS.map((b) => b.id);
    const poolA = banks[ids[0]] || [];
    const poolB = banks[ids[1]] || [];

    const [nA, nB] = pickSplit(
        CONFIG.TOTAL_QUESTIONS,
        CONFIG.MIN_PER_DOC,
        CONFIG.MAX_PER_DOC,
        poolA.length,
        poolB.length
    );

    const chosen = shuffle([...sample(poolA, nA), ...sample(poolB, nB)]);

    const questions = chosen.map((q) => {
        const correctText = q.options[q.correctAnswer];
        return {
            id: q.id,
            documentId: q.documentId,
            documentTitle: q.documentTitle,
            section: q.section,
            subsection: q.subsection,
            page: q.page,
            question: q.question,
            options: shuffle(q.options),
            correctText,
            explanation: q.explanation || ""
        };
    });

    return {
        questions,
        answers: new Array(questions.length).fill(null),
        currentIndex: 0,
        endTime: Date.now() + CONFIG.DURATION_MINUTES * 60 * 1000,
        finished: false
    };
}

/* ---- Exam controller ---- */

const Exam = {
    state: null,
    _timerId: null,
    _onTimeUp: null,

    init(state, { onTimeUp }) {
        this.state = state;
        this._onTimeUp = onTimeUp;
        this.renderQuestion();
        this.renderNavigator();
        this.startTimer();
    },

    /* --- navigation --- */
    goTo(index) {
        if (index < 0 || index >= this.state.questions.length) return;
        this.state.currentIndex = index;
        this.persist();
        this.renderQuestion();
        this.renderNavigator();
    },

    next() {
        if (this.state.currentIndex < this.state.questions.length - 1) {
            this.goTo(this.state.currentIndex + 1);
        }
    },

    back() {
        if (this.state.currentIndex > 0) {
            this.goTo(this.state.currentIndex - 1);
        }
    },

    isLast() {
        return this.state.currentIndex === this.state.questions.length - 1;
    },

    selectAnswer(text) {
        this.state.answers[this.state.currentIndex] = text;
        this.persist();
        this.renderNavigator();
        this.updateNextLabel();
    },

    unansweredCount() {
        return this.state.answers.filter((a) => a === null).length;
    },

    /* --- rendering --- */
    renderQuestion() {
        const i = this.state.currentIndex;
        const q = this.state.questions[i];

        document.getElementById("q-current").textContent = i + 1;
        document.getElementById("q-total").textContent = this.state.questions.length;
        document.getElementById("q-meta").textContent =
            `${q.documentTitle} · ${q.section}`;
        document.getElementById("q-text").textContent = q.question;

        const form = document.getElementById("options-form");
        form.innerHTML = "";
        const selected = this.state.answers[i];

        q.options.forEach((opt, idx) => {
            const id = `opt-${idx}`;
            const label = document.createElement("label");
            label.className = "option" + (selected === opt ? " selected" : "");

            const input = document.createElement("input");
            input.type = "radio";
            input.name = "answer";
            input.id = id;
            input.value = opt;
            input.checked = selected === opt;
            input.addEventListener("change", () => this.selectAnswer(opt));

            const span = document.createElement("span");
            span.className = "option-text";
            span.textContent = opt;

            label.appendChild(input);
            label.appendChild(span);
            form.appendChild(label);
        });

        document.getElementById("btn-back").disabled = i === 0;
        this.updateNextLabel();
    },

    updateNextLabel() {
        const btn = document.getElementById("btn-next");
        btn.textContent = this.isLast() ? "Finish Exam" : "Next";
        btn.classList.toggle("btn-danger", this.isLast());
        btn.classList.toggle("btn-primary", !this.isLast());
    },

    renderNavigator() {
        const grid = document.getElementById("navigator-grid");
        grid.innerHTML = "";
        this.state.questions.forEach((_, idx) => {
            const cell = document.createElement("button");
            cell.type = "button";
            cell.className = "nav-cell";
            cell.textContent = idx + 1;
            if (idx === this.state.currentIndex) cell.classList.add("current");
            else if (this.state.answers[idx] !== null) cell.classList.add("answered");
            else cell.classList.add("unanswered");
            cell.addEventListener("click", () => this.goTo(idx));
            grid.appendChild(cell);
        });
    },

    /* --- timer --- */
    startTimer() {
        this.tick();
        this._timerId = setInterval(() => this.tick(), 1000);
    },

    stopTimer() {
        if (this._timerId) {
            clearInterval(this._timerId);
            this._timerId = null;
        }
    },

    tick() {
        const remaining = Math.max(0, this.state.endTime - Date.now());
        const totalSec = Math.floor(remaining / 1000);
        const mm = String(Math.floor(totalSec / 60)).padStart(2, "0");
        const ss = String(totalSec % 60).padStart(2, "0");
        const el = document.getElementById("timer");
        el.textContent = `${mm}:${ss}`;
        el.classList.toggle("timer-warning", totalSec <= 60);

        if (remaining <= 0) {
            this.stopTimer();
            if (typeof this._onTimeUp === "function") this._onTimeUp();
        }
    },

    persist() {
        Storage.save(this.state);
    }
};
