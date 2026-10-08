# Sprint Risk Research

Research workspace for early prediction of issue non-completion within a sprint, using TAWOS as the primary dataset.

## Stack

- FastAPI application organized with `APIRouter` modules.
- PostgreSQL as the normalized, queryable research datastore.
- SQLAlchemy and Alembic for application-owned schema and migrations.
- Docker Compose for the API and PostgreSQL development environment.
- `pgloader` for the initial MySQL-to-PostgreSQL transfer of TAWOS.

The upstream TAWOS release is a MySQL dump. The MySQL instance is only an import/source adapter; application and research queries target PostgreSQL. Raw downloaded data stays under `data/raw/` and is deliberately excluded from Git.

## Start the API and PostgreSQL

1. Copy `.env.example` to `.env` and adjust local credentials if needed. The checked-in defaults are for local development only.
2. Start the database and API:

   ```powershell
   docker compose up --build -d
   ```

3. Open the interactive API docs at <http://localhost:8000/docs>.

The liveness endpoint is `/api/v1/health/live`; database readiness is `/api/v1/health/ready`.

## TAWOS data setup and PostgreSQL migration

Download TAWOS v1.1 from the [UCL Research Data Repository](https://doi.org/10.5522/04/21308124), read its terms of use, and place the archive at `data/raw/TAWOS-v1.1.sql.zip`. Extract `TAWOS.sql` to `data/raw/unpacked/TAWOS.sql`. The import/migration scripts do not download or commit the dataset.

Start PostgreSQL and an isolated MySQL source initialized from the dump:

```powershell
docker compose up -d db
docker compose --profile migration up -d source-mysql
```

Wait until `source-mysql` is healthy; the initial 4.3 GB SQL import can take several minutes. Then migrate and verify the row counts:

```powershell
.\scripts\migrate_tawos_to_postgres.ps1 -SourceContainer tawos-source-mysql
.\scripts\validate_tawos_migration.ps1 -SourceContainer tawos-source-mysql
```

The migration script refuses to load into a PostgreSQL `public` schema that already contains tables, to avoid accidental overwrite. Use a fresh local database for a repeat migration. The source DB is accessed with a read-only account by `pgloader` and is not exposed on a host port.

After validation, start/restart the API:

```powershell
docker compose up --build -d api
```

Key endpoints:

- `GET /api/v1/dataset/summary`
- `GET /api/v1/dataset/projects?limit=50&offset=0`

The migration preserves the upstream tables in PostgreSQL schema `tawos_raw`; application-owned research metadata is separated into the `research` schema and managed with Alembic. Migration validation currently compares exact row counts across all 13 upstream tables.

## Local tests

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
```

## Two-Tier System Architecture

The research implements an end-to-end framework combining predictive machine learning with an evidence-grounded agent interface:

1. **Tier 1: ML Scorer & Policy Controller (CatBoost)**
   - Operates at Landmark $L = 0.40$ (40% sprint progress) to evaluate active in-flight candidate issues.
   - Applies an effort-aware capacity budget of $K = 2$ issues per sprint to prevent alert fatigue.
2. **Tier 2: Proactive Grounded Agent Interface (Gemini Flash)**
   - Triggered strictly by Tier 1 for prioritized high-risk candidates.
   - Executes read-only tool calls (`get_issue_evidence`) to retrieve historical timeline events.
   - Enforces full audit provenance and runs an independent `ClaimGrader` to verify 100% citation grounding and eliminate phantom claims.

## Key Empirical Results (Protocol E3 v2 - Full 50-Scenario Suite)

| Metric | Baseline A0 (Template) | A1 (Single Narrator) | A2 (Bounded Tool Agent) |
|---|---|---|---|
| **Evidence Recall** | 100.0% | 100.0% | **100.0%** (Full audit trail) |
| **Grounding Precision** | 100.0% | 100.0% | **100.0%** (Zero phantom claims) |
| **Numeric Accuracy** | 100.0% | 100.0% | **100.0%** |
| **Decision Accuracy** | 100.0% | 98.0% | **98.0%** |
| **Average Tool Calls** | 0.0 | 0.0 | **1.0 call** (`get_issue_evidence`) |
| **Inference Latency (p50)** | 0.00s | 1.67s | **2.67s** |

All 68/68 test suite assertions pass (`pytest tests -q`), covering negative controls, adversarial probes, and API robustness.

## Research documents

- [Main Proposal / Đề cương nghiên cứu](documents/De_cuong_du_bao_som_rui_ro_sprint.md)
- [Slide Presentation & Research Summary](documents/Khung_trinh_bay_slide_va_tong_hop_ket_qua.md)
- [Phase 1 Protocol](documents/Protocol_pha_1_chot_bai_toan_va_thiet_ke_du_lieu.md)
- [Agent Extension Protocol E3 v2](artifacts/agent_extension/agent_v2/eval_report.md)
- [Deep Research on AI Agent Integration](documents/Deep_research_AI_agent_canh_bao_som.md)
- [Agent Research Progress](documents/Agent_research_progress.md)

