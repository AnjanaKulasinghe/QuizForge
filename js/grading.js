/* grading.js — score the exam and build the detailed report */

const Grading = {
    /** Compute score and per-question results from an exam state. */
    grade(state) {
        const details = state.questions.map((q, i) => {
            const given = state.answers[i];
            const correct = given === q.correctText;
            return {
                index: i,
                question: q.question,
                given,
                correctText: q.correctText,
                correct,
                answered: given !== null,
                documentId: q.documentId,
                documentTitle: q.documentTitle,
                section: q.section,
                subsection: q.subsection,
                page: q.page,
                explanation: q.explanation
            };
        });

        const score = details.filter((d) => d.correct).length;
        const total = details.length;
        const percent = total ? Math.round((score / total) * 100) : 0;
        const passed = score >= CONFIG.PASS_MARK;

        return { score, total, percent, passed, details };
    },

    /** Render the results header and detailed report into the DOM. */
    render(result) {
        const header = document.getElementById("result-header");
        header.classList.toggle("pass", result.passed);
        header.classList.toggle("fail", !result.passed);

        document.getElementById("result-score").textContent =
            `${result.score} / ${result.total}`;
        document.getElementById("result-percent").textContent = `${result.percent}%`;
        document.getElementById("result-verdict").textContent =
            result.passed ? "PASS" : "FAIL";

        const report = document.getElementById("report");
        report.innerHTML = "";

        result.details.forEach((d) => {
            const item = document.createElement("article");
            item.className = "report-item " + (d.correct ? "correct" : "incorrect");

            const status = d.correct ? "Correct" : (d.answered ? "Incorrect" : "Not answered");

            const yourAnswer = d.answered ? escapeHtml(d.given) : "<em>No answer selected</em>";

            // Correct answer text: green when the user was right, red when wrong.
            const correctClass = d.correct ? "ans-correct" : "ans-wrong";
            const correctBlock =
                `<p class="ans-row"><span class="ans-label">Correct answer:</span> ` +
                `<span class="${correctClass}">${escapeHtml(d.correctText)}</span></p>`;

            const explanation = d.explanation
                ? `<p class="explanation">${escapeHtml(d.explanation)}</p>`
                : "";

            // Source link is required for incorrectly answered questions,
            // formatted as: Document name > Section name > Subsection name.
            let sourceBlock = "";
            if (!d.correct) {
                const source = `${d.documentTitle} > ${d.section} > ${d.subsection}`;
                const pdf = pdfForDocument(d.documentId);
                const sourceLink = pdf
                    ? `<a href="${pdf}#page=${d.page}" target="_blank" rel="noopener">${escapeHtml(source)}</a>`
                    : escapeHtml(source);
                sourceBlock = `<p class="source"><span class="ans-label">Source:</span> ${sourceLink}</p>`;
            }

            item.innerHTML =
                `<header class="report-item-head">` +
                `<span class="report-num">Question ${d.index + 1}</span>` +
                `<span class="report-status">${status}</span>` +
                `</header>` +
                `<p class="report-question">${escapeHtml(d.question)}</p>` +
                `<p class="ans-row"><span class="ans-label">Your answer:</span> ` +
                `<span class="ans-given">${yourAnswer}</span></p>` +
                correctBlock +
                explanation +
                sourceBlock;

            report.appendChild(item);
        });
    }
};

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}
