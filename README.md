# Loan Application Agent

A local training demo for preparing mock loan applications. The desktop client uses Tkinter, the REST API uses FastAPI, LangChain tools expose the workflow to an agent, and SQLite stores fictional sample customers and applications.

This project is mock-only. It does not connect to a bank, submit real applications, or require real customer data. Every new application starts as a draft. A submission request is rejected unless `confirmation` is explicitly `true`.

## Setup

Use Python 3.10 or newer:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run

Start the API from the project directory:

```powershell
python -m uvicorn app.api:app --reload
```

In another terminal, with the same virtual environment active, start the desktop client:

```powershell
python -m app.desktop
```

The local API documentation is available at http://127.0.0.1:8000/docs. The SQLite database is created at `data/loan_agent.db`; set `LOAN_AGENT_DB_PATH` to use another local file.

To point the desktop client at a deployed API, set `LOAN_AGENT_API_URL` to its base URL before starting the client. If unset, it uses the local API URL above.

## Deploy on Render

The `render.yaml` Blueprint deploys the FastAPI service. In Render, create a new Blueprint and select this GitHub repository. After deployment, open the service URL at `/docs` to use the REST API.

The free web service uses an ephemeral filesystem, so its SQLite database can reset when the service restarts or redeploys. This deployment is for mock training data only, not production or real customer applications. Keep the desktop client local and set `LOAN_AGENT_API_URL` to the Render service URL if you want it to use the hosted mock API.

## API workflow

1. `GET /customers` lists fictional training records.
2. `POST /applications` creates a draft and never submits it.
3. Review the draft with `GET /applications/{id}`.
4. Only after explicit user approval, call `POST /applications/{id}/submit` with `{"confirmation": true}`. A missing or false confirmation is rejected.

The LangChain tools in `app/tools.py` follow the same boundary: `create_loan_application` only creates drafts, while `submit_loan_application` requires a confirmation argument.

## Tests

```powershell
python -m pytest
```
