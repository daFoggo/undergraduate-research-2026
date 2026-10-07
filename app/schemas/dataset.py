from pydantic import BaseModel, ConfigDict


class DatasetSummary(BaseModel):
    dataset: str
    schema_name: str
    projects: int
    sprints: int
    issues: int
    change_log_entries: int
    comments: int


class ProjectSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_key: str | None
    name: str | None
    issue_count: int
    sprint_count: int

