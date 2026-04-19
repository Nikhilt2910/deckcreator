# DeckCreator Full Stack App

Production-ready full-stack structure with:

- FastAPI backend
- Next.js frontend
- Excel to PowerPoint generation
- Ticketing, approval, email, and git automation

## Folders

```text
.
|-- app/
|   `-- ...
|-- backend/
|   `-- app/
|       |-- api/
|       |   |-- approval.py
|       |   |-- ticket.py
|       |   `-- upload.py
|       |-- core/
|       |   `-- config.py
|       |-- models/
|       |-- services/
|       |   |-- ai_service.py
|       |   |-- email_service.py
|       |   |-- excel_service.py
|       |   |-- git_service.py
|       |   `-- ppt_service.py
|       `-- main.py
|-- frontend/
|   |-- app/
|   |   |-- status/
|   |   |   `-- page.tsx
|   |   |-- tickets/
|   |   |   `-- page.tsx
|   |   |-- upload/
|   |   |   `-- page.tsx
|   |   |-- globals.css
|   |   |-- layout.tsx
|   |   `-- page.tsx
|   |-- lib/
|   |   `-- api.ts
|   |-- next.config.ts
|   |-- package.json
|   `-- tsconfig.json
|-- data/
|-- templates/
|-- static/
|-- tests/
|-- main.py
|-- README.md
`-- requirements.txt
```

## Local Development

Backend:

```powershell
uvicorn app.main:app --reload --port 8000
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Frontend environment:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Dependencies

- `fastapi`: API framework.
- `uvicorn[standard]`: local ASGI server.
- `pandas`: workbook data handling and analysis.
- `openpyxl`: Excel engine for `.xlsx` files.
- `python-pptx`: PowerPoint template and generation support.
- `python-multipart`: multipart form upload support.
- `httpx`: test client transport for local API verification.
- `openai`: sends business data to the OpenAI API for analysis.

## API

### `POST /upload`

Multipart form fields:

- `excel_file`: Excel workbook (`.xlsx`, `.xls`, `.xlsm`)
- `reference_file`: PowerPoint or PDF reference (`.pptx`, `.potx`, `.pdf`)

Behavior:

- validates extensions
- saves the Excel file under `data/uploads/excel/`
- saves the reference file under `data/uploads/templates/`
- returns a success response with saved file metadata

### `POST /reports/generate`

Multipart form fields:

- `excel_file`: Excel workbook (`.xlsx`, `.xls`, `.xlsm`)
- `reference_file`: PowerPoint or PDF reference (`.pptx`, `.potx`, `.pdf`)

Behavior:

- parses workbook data into structured summaries, rankings, and sample rows
- sends those summaries to OpenAI for executive analysis
- generates KPI, performance, campaign, summary, insight, and sample-data slides
- matches style from a PPTX reference when available
- accepts PDF as a reference input and falls back to a clean generated deck
- saves the output under `data/output/`
- returns the generated `.pptx` as a downloadable file

The backend keeps the existing routes and also exposes:

- `POST /api/upload`
- `POST /api/ticket`
- `GET /api/ticket/{ticket_id}`
- `GET /api/approve`
- `GET /api/reject`

## Deploy

### Docker

Build and run locally:

```powershell
docker build -t deckcreator .
docker run --env-file .env -p 8000:8000 deckcreator
```

### Render

This repo includes [render.yaml](/C:/Users/nikhi/PycharmProjects/PythonProject/render.yaml) for a web service deployment from GitHub.

Required environment variables on the platform:

- `APP_BASE_URL`
- `OPENAI_API_KEY`
- `JIRA_BASE_URL`
- `JIRA_EMAIL`
- `JIRA_API_TOKEN`
- `JIRA_PROJECT_KEY`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_FROM_EMAIL`

Optional:

- `GITHUB_REPO_URL`
- `GITHUB_BRANCH`
- `OPENAI_ENGINEERING_MODEL`
- `OPENAI_ANALYSIS_MODEL`
- `FRONTEND_APP_URL`

Recommended model defaults:

- `OPENAI_ANALYSIS_MODEL=gpt-5.2`
- `OPENAI_ENGINEERING_MODEL=gpt-5.2-codex`

These defaults are aligned with the current OpenAI API model docs, which recommend `gpt-5.2` for most API usage and position `gpt-5.2-codex` as the upgraded coding model for agentic coding tasks:

- https://platform.openai.com/docs/guides/latest-model
- https://platform.openai.com/docs/models/gpt-5.2-codex

Deployment flow:

1. Push the latest code to GitHub.
2. Create a new Render Blueprint or Web Service from the GitHub repo.
3. Set the environment variables in the Render dashboard.
4. Deploy and verify `/health`.
