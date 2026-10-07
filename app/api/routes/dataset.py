from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.dataset import DatasetSummary, ProjectSummary

router = APIRouter(prefix="/dataset", tags=["dataset"])


@router.get("/summary", response_model=DatasetSummary)
def dataset_summary(db: Session = Depends(get_db)) -> DatasetSummary:
    table_names = ("project", "sprint", "issue", "change_log", "comment")
    existing = {
        row[0]
        for row in db.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'tawos_raw' AND table_name = ANY(:names)"
            ),
            {"names": list(table_names)},
        )
    }
    missing = sorted(set(table_names) - existing)
    if missing:
        raise HTTPException(
            status_code=503,
            detail=f"TAWOS tables are not fully imported into tawos_raw: {', '.join(missing)}",
        )

    counts = {
        table: db.execute(text(f"SELECT count(*) FROM tawos_raw.{table}")).scalar_one()
        for table in table_names
    }
    return DatasetSummary(
        dataset="TAWOS v1.1",
        schema_name="tawos_raw",
        projects=counts["project"],
        sprints=counts["sprint"],
        issues=counts["issue"],
        change_log_entries=counts["change_log"],
        comments=counts["comment"],
    )


@router.get("/projects", response_model=list[ProjectSummary])
def list_projects(
    search: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[ProjectSummary]:
    statement = text(
        """
        SELECT p.id, p.project_key, p.name,
               COALESCE(i.issue_count, 0)::int AS issue_count,
               COALESCE(s.sprint_count, 0)::int AS sprint_count
        FROM tawos_raw.project AS p
        LEFT JOIN (
            SELECT project_id, count(*) AS issue_count
            FROM tawos_raw.issue
            GROUP BY project_id
        ) AS i ON i.project_id = p.id
        LEFT JOIN (
            SELECT project_id, count(*) AS sprint_count
            FROM tawos_raw.sprint
            GROUP BY project_id
        ) AS s ON s.project_id = p.id
        WHERE (CAST(:search AS text) IS NULL
               OR p.name ILIKE CAST(:pattern AS text)
               OR p.project_key ILIKE CAST(:pattern AS text))
        ORDER BY p.name NULLS LAST, p.id
        LIMIT :limit OFFSET :offset
        """
    )
    try:
        rows = db.execute(
            statement,
            {
                "search": search,
                "pattern": f"%{search}%" if search else None,
                "limit": limit,
                "offset": offset,
            },
        ).mappings()
        return [ProjectSummary.model_validate(row) for row in rows]
    except ProgrammingError as exc:
        raise HTTPException(
            status_code=503,
            detail="TAWOS source tables are not available yet; finish the data migration first.",
        ) from exc
