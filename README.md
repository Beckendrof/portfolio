# VT220 Terminal Portfolio

A retro VT220 terminal-style portfolio website that auto-generates from your resume PDF using the Anthropic API.

## Quick Start

1. Clone the repo
2. `python3 -m venv venv && source venv/bin/activate`
3. `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and add your `ANTHROPIC_API_KEY`
5. Add `resume.pdf` to the project root
6. `python scripts/parse_resume.py` — extracts data to `data/resume.json`
7. `python scripts/build.py` — builds `dist/index.html`
8. Open `dist/index.html` in browser to preview

## Auto-update locally

- Run `python watch.py`
- Save a new `resume.pdf` to the folder — the pipeline runs automatically (parse, build, commit, push)

## Deploy to Netlify (recommended)

1. Push the repo to GitHub
2. Go to [app.netlify.com](https://app.netlify.com) → **Add new site → Import an existing project**
3. Connect your GitHub account and select this repo
4. Netlify auto-detects `netlify.toml` — build command and publish dir are pre-configured
5. Go to **Site settings → Environment variables** and add `ANTHROPIC_API_KEY`
6. Click **Deploy site** — your portfolio is live at `https://<your-site>.netlify.app`

On every push to `main`, GitHub Actions parses the resume (if changed) and rebuilds `dist/index.html`. Netlify picks up the updated `dist/` automatically.

## Deploy to GitHub Pages (alternative)

1. Push the repo to GitHub
2. Go to **Settings > Pages > Source: Deploy from a branch**, select `main` / `dist` folder
3. Add `ANTHROPIC_API_KEY` to **Settings > Secrets and variables > Actions**
4. Push any change to trigger a deploy

## Updating your resume

**Option A (local watcher running):** Just save the new PDF to the folder. Done.

**Option B (no watcher):** Replace `resume.pdf`, then `git add . && git commit -m "update resume" && git push`. GitHub Actions handles the rest.

## Project Structure

```
portfolio/
├── resume.pdf                  # Drop updated resume here
├── src/template.html           # VT220 terminal HTML template
├── scripts/
│   ├── parse_resume.py         # PDF -> resume.json via Anthropic API
│   └── build.py                # resume.json -> dist/index.html
├── data/resume.json            # Auto-generated structured data
├── dist/index.html             # Final built output (served by Pages)
├── .github/workflows/deploy.yml
├── watch.py                    # Local file watcher
├── requirements.txt
└── .env.example
```
