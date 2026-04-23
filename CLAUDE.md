# Claude Code: VT220 Terminal Portfolio Project

I have a VT220 terminal-style portfolio as a single HTML file (`portfolio.html`) in this folder. I also have my resume as `resume.pdf` in the same folder. I want to turn this into a proper project that:

1. Parses my resume PDF using the Anthropic API (Claude) to extract structured JSON
2. Uses that JSON to regenerate the terminal portfolio HTML automatically
3. Deploys to GitHub Pages for free hosting
4. Auto-rebuilds via GitHub Actions whenever I push a new resume.pdf
5. Has a local file watcher that detects when I save a new resume.pdf and auto-commits + pushes to trigger the pipeline

Build the entire project from scratch in the current directory. Here is the exact spec:

---

## PROJECT STRUCTURE

```
portfolio/
├── resume.pdf                  # I drop updated resume here — never touch manually
├── src/
│   └── template.html           # The VT220 terminal HTML (from portfolio.html but with data extracted into a Python-injectable section)
├── scripts/
│   ├── parse_resume.py         # PDF → resume.json using Anthropic API
│   └── build.py                # resume.json → dist/index.html (injects data into template)
├── data/
│   └── resume.json             # Auto-generated, committed to git so Pages can serve without a build step
├── dist/
│   └── index.html              # Final built output, committed to git for GitHub Pages
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions: parse → build → commit dist → Pages deploys
├── watch.py                    # Local watcher: detects resume.pdf change → runs full pipeline → git push
├── requirements.txt
├── .env.example                # ANTHROPIC_API_KEY=your_key_here
├── .gitignore
└── README.md                   # Clear setup instructions
```

---

## STEP 1 — parse_resume.py

Use the Anthropic Python SDK to send `resume.pdf` to `claude-haiku-4-5-20251001` as a base64-encoded PDF document and extract structured JSON.

The prompt to Claude should request this exact JSON schema:

```json
{
  "name": "string",
  "title": "string",
  "location": "string",
  "email": "string",
  "phone": "string",
  "github": "string (username only, no URL prefix)",
  "linkedin": "string (slug only, e.g. abhinav-parameshwaran)",
  "summary": "string",
  "experience": [
    {
      "title": "string",
      "company": "string",
      "location": "string",
      "start": "string",
      "end": "string (or Present)",
      "bullets": ["string"]
    }
  ],
  "education": [
    {
      "degree": "string",
      "school": "string",
      "date": "string"
    }
  ],
  "skills": {
    "category_name": ["skill1", "skill2"]
  },
  "projects": [
    {
      "name": "string",
      "slug": "string (lowercase, hyphenated, for use as command argument)",
      "description": "string (2-3 sentences)",
      "tech": ["string"],
      "url": "string (full GitHub URL if present, else empty string)"
    }
  ]
}
```

The script should:
- Load `ANTHROPIC_API_KEY` from environment (python-dotenv for local, GitHub secret for CI)
- Accept an optional `--resume` path argument (default: `resume.pdf`)
- Accept an optional `--output` path argument (default: `data/resume.json`)
- Print a success message with timestamp on completion
- Handle errors gracefully (missing file, API error, JSON parse failure)

---

## STEP 2 — src/template.html

Take `portfolio.html` (which is in this folder) and refactor it so that all personal data (name, commands, experience bullets, projects list, contact info, etc.) is NOT hardcoded in the HTML.

Instead, add a single `<script id="resume-data" type="application/json">` tag near the top of `<body>` that will be injected by the build script. The VT220 terminal JavaScript should read from this JSON tag at runtime to populate all commands (about, skills, experience, projects, contact, neofetch, etc.) dynamically.

The template should have a clear injection marker comment so `build.py` knows exactly where to insert the JSON:
```html
<!-- RESUME_DATA_INJECT -->
<script id="resume-data" type="application/json">
{}
</script>
<!-- /RESUME_DATA_INJECT -->
```

The terminal JavaScript should be updated to read this data:
```js
const RESUME = JSON.parse(document.getElementById('resume-data').textContent);
```

And all command handlers should use RESUME fields instead of hardcoded strings. For example:
- `about` command → uses RESUME.name, RESUME.title, RESUME.location, RESUME.summary
- `experience` → iterates RESUME.experience
- `projects` → iterates RESUME.projects; `projects <slug>` finds by slug
- `skills` → iterates RESUME.skills object
- `contact` → RESUME.email, RESUME.phone, RESUME.github, RESUME.linkedin
- `github` command → opens `https://github.com/${RESUME.github}`
- `linkedin` command → opens `https://www.linkedin.com/in/${RESUME.linkedin}`
- `email` command → mailto link using RESUME.email
- `neofetch` → uses RESUME.name, RESUME.title, RESUME.location
- The boot banner should display RESUME.name and RESUME.title
- `whoami` should return RESUME.name

---

## STEP 3 — scripts/build.py

Simple script that:
1. Reads `data/resume.json`
2. Reads `src/template.html`
3. Replaces the content between `<!-- RESUME_DATA_INJECT -->` and `<!-- /RESUME_DATA_INJECT -->` with the injected script tag containing the JSON
4. Writes the result to `dist/index.html`
5. Creates `dist/` if it doesn't exist
6. Prints success message with timestamp

Also inject the build timestamp into the HTML as an HTML comment at the top:
```html
<!-- Built: 2026-04-22T14:23:00Z from resume.json -->
```

---

## STEP 4 — watch.py

A local file watcher using the `watchdog` library that:
1. Watches the project root for changes to `resume.pdf`
2. When a change is detected, waits 1 second (debounce) then:
   a. Runs `python scripts/parse_resume.py`
   b. Runs `python scripts/build.py`
   c. Runs `git add data/resume.json dist/index.html resume.pdf`
   d. Runs `git commit -m "auto: update portfolio from resume ($(date))"`
   e. Runs `git push`
3. Prints clear status messages at each step with timestamps
4. Handles errors at each step without crashing (prints error, waits for next change)
5. Shows a startup message: "Watching for resume.pdf changes. Drop a new PDF to auto-deploy."

---

## STEP 5 — .github/workflows/deploy.yml

GitHub Actions workflow that:
- Triggers on: push to `main` branch
- Condition: only run the parse step if `resume.pdf` was changed in the commit; always run build + deploy
- Jobs:
  1. **parse** (conditional on resume.pdf change):
     - Uses `ubuntu-latest`
     - Sets up Python 3.11
     - Installs requirements
     - Runs `parse_resume.py` with `ANTHROPIC_API_KEY` from GitHub Secrets
     - Commits and pushes updated `data/resume.json` back to main
  2. **build-and-deploy**:
     - Depends on parse (or skips it if resume unchanged)
     - Runs `build.py`
     - Deploys `dist/` to GitHub Pages using the official `actions/deploy-pages@v4` action

Use proper GitHub Actions permissions (contents: write for commit-back, pages: write for deployment).

Make the workflow robust: if parse fails (e.g. API key missing), the build should still run with the existing `data/resume.json`.

---

## STEP 6 — requirements.txt

```
anthropic>=0.40.0
python-dotenv>=1.0.0
watchdog>=4.0.0
```

---

## STEP 7 — .gitignore

```
.env
__pycache__/
*.pyc
.DS_Store
node_modules/
```

Do NOT gitignore `dist/` or `data/` — these need to be committed so GitHub Pages can serve them and so the build step has the latest data.

---

## STEP 8 — README.md

Write a clear README with:

### Quick Start
1. Clone the repo
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and add your `ANTHROPIC_API_KEY`
4. Add `resume.pdf` to the project root
5. `python scripts/parse_resume.py` — extracts data
6. `python scripts/build.py` — builds `dist/index.html`
7. Open `dist/index.html` in browser to preview

### Auto-update locally
- Run `python watch.py`
- Save a new `resume.pdf` to the folder — pipeline runs automatically

### Deploy to GitHub Pages
1. Push the repo to GitHub
2. Go to Settings → Pages → Source: GitHub Actions
3. Add `ANTHROPIC_API_KEY` to Settings → Secrets → Actions
4. Push any change to trigger a deploy
5. Your portfolio lives at `https://<username>.github.io/<repo>/`

### Updating your resume
**Option A (local watcher running):** Just save the new PDF to the folder. Done.
**Option B (no watcher):** Replace `resume.pdf`, then `git add . && git commit -m "update resume" && git push`. GitHub Actions handles the rest.

---

## IMPORTANT NOTES FOR IMPLEMENTATION

- Start by reading `portfolio.html` in full to understand the existing terminal structure before modifying anything
- The template refactor must preserve 100% of the VT220 visual aesthetic (CRT effects, scanlines, phosphor glow, blinking cursor, boot sequence, all commands)
- The boot sequence login animation should use RESUME.name dynamically
- The `projects <slug>` command must still work with tab completion — build the completions list from `RESUME.projects.map(p => p.slug)` at runtime
- After building, do a quick sanity check: open `dist/index.html` and verify the terminal boots and the `about` command returns the correct name from the JSON
- The `data/resume.json` should be pretty-printed (indent=2) for readability
- In the GitHub Actions workflow, use `git config user.email "actions@github.com"` and `git config user.name "GitHub Actions"` for the commit-back step
- Make sure the workflow handles the case where `data/resume.json` already exists and is unchanged (don't create an empty commit)

Begin by reading `portfolio.html` in full, then execute all steps in order.
