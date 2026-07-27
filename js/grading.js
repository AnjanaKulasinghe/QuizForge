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
                domain: q.domain,
                objective: q.objective,
                references: q.references,
                options: q.options,
                optionExplanations: q.optionExplanations,
                explanation: q.explanation
            };
        });

        const score = details.filter((d) => d.correct).length;
        const total = details.length;
        const percent = total ? Math.round((score / total) * 100) : 0;
        const passed = CONFIG.PASS_PERCENT != null
            ? (total > 0 && (score / total) * 100 >= CONFIG.PASS_PERCENT)
            : score >= CONFIG.PASS_MARK;

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

        this.renderSummary(result);

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

            // Per-option explanation breakdown (Security+-style questions).
            let optionReview = "";
            if (d.optionExplanations && Array.isArray(d.options)) {
                const rows = d.options.map((opt) => {
                    const isCorrect = opt === d.correctText;
                    const isChosenWrong = d.answered && opt === d.given && !isCorrect;
                    let cls = "opt-review";
                    if (isCorrect) cls += " opt-correct";
                    else if (isChosenWrong) cls += " opt-chosen-wrong";

                    let badge = "";
                    if (isCorrect) badge = `<span class="opt-badge badge-correct">Correct</span>`;
                    else if (isChosenWrong) badge = `<span class="opt-badge badge-chosen">Your answer</span>`;

                    const why = d.optionExplanations[opt]
                        ? `<p class="opt-why">${escapeHtml(d.optionExplanations[opt])}</p>`
                        : "";

                    return `<li class="${cls}"><div class="opt-head">` +
                        `<span class="opt-text">${escapeHtml(opt)}</span>${badge}` +
                        `</div>${why}</li>`;
                }).join("");
                optionReview = `<ul class="option-review">${rows}</ul>`;
            }

            // Source link is shown for incorrectly answered questions. Prefer a
            // PDF page link, then explicit references, then a text breadcrumb.
            let sourceBlock = "";
            if (!d.correct) {
                const pdf = pdfForDocument(d.documentId);
                if (pdf) {
                    const source = `${d.documentTitle} > ${d.section} > ${d.subsection}`;
                    const sourceLink =
                        `<a href="${pdf}#page=${d.page}" target="_blank" rel="noopener">${escapeHtml(source)}</a>`;
                    sourceBlock = `<p class="source"><span class="ans-label">Source:</span> ${sourceLink}</p>`;
                } else if (Array.isArray(d.references) && d.references.length) {
                    const refs = d.references.map(escapeHtml).join(", ");
                    sourceBlock = `<p class="source"><span class="ans-label">Reference:</span> ${refs}</p>`;
                } else if (d.documentTitle) {
                    const source = `${d.documentTitle} > ${d.section} > ${d.subsection}`;
                    sourceBlock = `<p class="source"><span class="ans-label">Source:</span> ${escapeHtml(source)}</p>`;
                }
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
                optionReview +
                sourceBlock;

            report.appendChild(item);
        });
    },

    /** Build a per-domain performance breakdown so users can spot weak areas. */
    renderSummary(result) {
        const container = document.getElementById("result-summary");
        if (!container) return;

        const groups = new Map();
        result.details.forEach((d) => {
            const key = d.domain || "Uncategorized";
            let g = groups.get(key);
            if (!g) {
                g = { domain: key, total: 0, correct: 0, incorrect: 0, unanswered: 0 };
                groups.set(key, g);
            }
            g.total += 1;
            if (d.correct) g.correct += 1;
            else if (d.answered) g.incorrect += 1;
            else g.unanswered += 1;
        });

        const total = result.total || 1;
        const rows = [...groups.values()]
            .sort((a, b) => (a.correct / a.total) - (b.correct / b.total));

        // Highlight the weakest area (lowest accuracy with at least one question).
        const weakest = rows.length ? rows[0] : null;

        const bodyRows = rows.map((g) => {
            const share = Math.round((g.total / total) * 100);
            const acc = Math.round((g.correct / g.total) * 100);
            const wrong = 100 - acc;
            const isWeak = weakest && g.domain === weakest.domain && acc < 100;
            return `<tr class="${isWeak ? "summary-weak" : ""}">` +
                `<td class="summary-domain">${escapeHtml(g.domain)}` +
                `${isWeak ? ` <span class="summary-flag">Focus area</span>` : ""}</td>` +
                `<td class="summary-num">${share}%</td>` +
                `<td class="summary-num">${g.total}</td>` +
                `<td class="summary-num summary-ok">${g.correct}</td>` +
                `<td class="summary-num summary-bad">${g.incorrect}</td>` +
                `<td class="summary-num">${g.unanswered}</td>` +
                `<td class="summary-acc">` +
                `<div class="summary-bar"><span class="summary-bar-fill" style="width:${acc}%"></span></div>` +
                `<span class="summary-acc-val">${acc}% correct / ${wrong}% wrong</span>` +
                `</td>` +
                `</tr>`;
        }).join("");

        const advice = weakest && Math.round((weakest.correct / weakest.total) * 100) < 100
            ? `<p class="summary-advice">You scored lowest in ` +
            `<strong>${escapeHtml(weakest.domain)}</strong> ` +
            `(${Math.round((weakest.correct / weakest.total) * 100)}% correct). ` +
            `Focus your study there first.</p>`
            : `<p class="summary-advice">Strong, balanced performance across all areas.</p>`;

        container.innerHTML =
            `<h2 class="summary-title">Exam Summary</h2>` +
            `<p class="summary-lede">You answered <strong>${result.score}</strong> of ` +
            `<strong>${result.total}</strong> questions correctly ` +
            `(<strong>${result.percent}%</strong>). Breakdown by category:</p>` +
            `<div class="summary-table-wrap"><table class="summary-table">` +
            `<thead><tr>` +
            `<th>Category</th><th>Share</th><th>Qs</th>` +
            `<th>Correct</th><th>Wrong</th><th>Skipped</th><th>Accuracy</th>` +
            `</tr></thead>` +
            `<tbody>${bodyRows}</tbody>` +
            `</table></div>` +
            advice;
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
