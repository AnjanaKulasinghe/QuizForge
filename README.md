# QuizForge

A lightweight, zero-dependency practice exam engine for the browser. QuizForge draws random questions from one or more question banks, runs a timed exam, saves progress automatically, and produces a detailed, printable results report with source references back into the original documents.

The current deployment is configured as a practice exam for the **WKF Kumite** and **Kata Competition Rules (2026)**, but the engine is document-agnostic — swap the question banks and PDFs to quiz on any subject.

**Live site:** [quizforge.koungasolutions.co.nz](https://quizforge.koungasolutions.co.nz)

---

## Features

- **Randomised exams** — 30 questions drawn from a pool of 1,000 (500 per document), with a randomised split between the two source documents on every attempt.
- **Timed with auto-submit** — a 30-minute countdown starts on *Start Exam* and auto-submits at `0:00`.
- **Auto-save & resume** — in-progress exams are persisted to `localStorage`, so a refresh or accidental tab close won't lose your work.
- **Question navigator** — jump to any question and see answered / unanswered / current status at a glance.
- **Detailed results report** — per-question breakdown showing your answer, the correct answer, an explanation, and a deep link to the exact page/section of the source PDF for anything you got wrong.
- **Print / PDF export** — a dedicated print stylesheet produces a clean report for download or printing.
- **No build step, no dependencies** — plain HTML, CSS and vanilla JavaScript. Just serve the folder.

---

## Project structure

```
QuizForge/
├── index.html                 # App shell: welcome, exam and results views
├── styles.css                 # Screen styles
├── print.css                  # Print / PDF report styles
├── CNAME                       # Custom domain for GitHub Pages
├── assets/                     # Logos and source rule PDFs
│   ├── QuizForge.png
│   ├── koungasolutions.png
│   ├── kumite-rules.pdf        # (git-ignored)
│   └── kata-rules.pdf          # (git-ignored)
├── data/                       # Generated question banks (served at runtime)
│   ├── questions-kumite.json   # 500 questions
│   └── questions-kata.json     # 500 questions
├── js/
│   ├── data.js                 # CONFIG + question-bank loading
│   ├── storage.js              # localStorage persistence
│   ├── exam.js                 # Exam construction, rendering, navigation, timer
│   ├── grading.js              # Scoring and results report
│   └── app.js                  # View routing and event wiring
└── build/                      # Question-bank generator (git-ignored)
    ├── gen_questions.py        # Builds the JSON banks from rule facts
    ├── kumite.txt / kata.txt   # Source rule text
    └── kumite.json / kata.json
```

---

## Running locally

The app fetches JSON at runtime, so it must be served over HTTP — opening `index.html` directly with `file://` will fail with a load error.

```bash
# from the project root
python3 -m http.server 8000
```

Then open <http://localhost:8000/>.

Any static file server works (e.g. `npx serve`, VS Code Live Server, nginx).

---

## How it works

1. **Load** — on startup, `app.js` calls `loadBanks()` in [js/data.js](js/data.js) to fetch each bank listed in `CONFIG.BANKS`. If a saved in-progress exam is found, a *Resume* banner is shown.
2. **Build** — `buildExam()` in [js/exam.js](js/exam.js) picks a randomised split between the two documents (each contributing 12–18 of the 30 questions), samples questions, and shuffles both the question order and each question's options.
3. **Run** — the `Exam` controller renders one question at a time, tracks answers, updates the navigator, and manages the countdown timer. State is persisted after every change.
4. **Grade** — on submit (manual or timed-out), `Grading.grade()` in [js/grading.js](js/grading.js) scores the exam and `Grading.render()` builds the report. A score of `≥ PASS_MARK` (27/30 = 90%) is a pass.

### Configuration

All exam parameters live in `CONFIG` at the top of [js/data.js](js/data.js):

| Setting            | Default | Meaning                                            |
| ------------------ | ------- | -------------------------------------------------- |
| `TOTAL_QUESTIONS`  | `30`    | Questions per exam                                 |
| `DURATION_MINUTES` | `30`    | Exam length                                        |
| `PASS_MARK`        | `27`    | Correct answers needed to pass (90%)               |
| `MIN_PER_DOC`      | `12`    | Minimum questions drawn from each document         |
| `MAX_PER_DOC`      | `19`    | Upper bound for the per-document split              |
| `STORAGE_KEY`      | —       | `localStorage` key for the in-progress exam        |
| `BANKS`            | —       | List of `{ id, file, pdf }` question-bank sources  |

---

## Question bank format

Each bank is a JSON array of question objects:

```json
{
  "id": "KUMITE-Q0001",
  "documentId": "kumite",
  "documentTitle": "WKF Kumite Competition Rules",
  "section": "Article 14: Video Review Request",
  "subsection": "14.11",
  "page": 39,
  "difficulty": "applied",
  "question": "If a video review request is found invalid, what is the consequence for the coach?",
  "options": [
    "The coach loses the right to raise another video request for the rest of the bout",
    "Nothing – the card is always retained",
    "The coach's athlete receives a warning",
    "The athlete is disqualified"
  ],
  "correctAnswer": 0,
  "explanation": "Article 14.11: if the request is invalid, the coach loses the right to raise another video request for the remainder of the bout."
}
```

| Field           | Type     | Description                                                       |
| --------------- | -------- | ---------------------------------------------------------------- |
| `id`            | string   | Unique question identifier                                       |
| `documentId`    | string   | Bank id; maps to a PDF via `CONFIG.BANKS`                         |
| `documentTitle` | string   | Human-readable document name (shown in the report)               |
| `section`       | string   | Article / section reference                                      |
| `subsection`    | string   | Subsection reference                                             |
| `page`          | number   | Page number for the PDF deep link (`#page=N`)                    |
| `difficulty`    | string   | Difficulty tag (e.g. `theory`, `applied`)                        |
| `question`      | string   | Question stem                                                    |
| `options`       | string[] | Answer choices (order is shuffled at runtime)                    |
| `correctAnswer` | number   | Index into `options` of the correct choice                       |
| `explanation`   | string   | Shown in the report to explain the answer                        |

### Regenerating the banks

The banks are generated from structured rule facts by [build/gen_questions.py](build/gen_questions.py), which expands each fact into paraphrased variants while preserving a real Article/subsection/page reference:

```bash
cd build
python3 gen_questions.py
```

> Note: the `build/` folder and `*.pdf` files are git-ignored. The committed `data/*.json` banks are the generated output consumed by the app.

---

## Customising for a different subject

1. Replace the PDFs in `assets/` and update the `pdf` paths in `CONFIG.BANKS`.
2. Generate or hand-author new `data/questions-*.json` banks in the format above.
3. Update `CONFIG.BANKS` with your bank `id`, `file` and `pdf`.
4. Adjust `TOTAL_QUESTIONS`, `DURATION_MINUTES`, `PASS_MARK` and the per-document split to taste.

---

## Deployment

The site is a static bundle deployed via **GitHub Pages** with a custom domain (see [CNAME](CNAME)). Push to the deployment branch and Pages serves the root of the repo. The source PDFs referenced by the report links must be present in `assets/` on the server (they are excluded from version control by default).

---

## Tech stack

- HTML5, CSS3 (custom properties, print stylesheet)
- Vanilla JavaScript (ES6+, no framework, no bundler)
- `localStorage` for persistence
- Python 3 for offline question-bank generation

---

## License

© Kounga Solutions. All rights reserved.

Powered by [Kounga Solutions](https://koungasolutions.co.nz).
