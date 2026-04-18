# Excel To PowerPoint API

Clean modular FastAPI project structure for an app that:

- accepts Excel files
- analyzes data
- generates PowerPoint presentations
- exposes a simple API

## Folders

```text
.
|-- app/
|   |-- api/
|   |   `-- routes/
|   |       |-- health.py
|   |       `-- uploads.py
|   |-- core/
|   |   `-- config.py
|   |-- schemas/
|   |   `-- upload.py
|   |-- services/
|   |   |-- analysis_service.py
|   |   |-- excel_service.py
|   |   |-- ppt_service.py
|   |   |-- presentation_service.py
|   |   `-- upload_service.py
|   |-- utils/
|   |   `-- file_manager.py
|   `-- main.py
|-- data/
|   |-- output/
|   `-- uploads/
|       |-- excel/
|       `-- templates/
|-- main.py
|-- README.md
`-- requirements.txt
```

## Main files

- `app/main.py`: FastAPI application entrypoint.
- `app/api/routes/uploads.py`: `POST /upload` endpoint.
- `app/services/upload_service.py`: validates files and saves them locally.
- `app/services/excel_service.py`: Excel loading/preview utilities for later analysis.
- `app/services/analysis_service.py`: placeholder analysis workflow module.
- `app/services/presentation_service.py`: placeholder PowerPoint generation workflow module.
- `app/services/ppt_service.py`: PowerPoint template loader.
- `app/core/config.py`: central filesystem paths.
- `app/utils/file_manager.py`: safe local file persistence helper.

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

## Run

```powershell
uvicorn app.main:app --reload
```
