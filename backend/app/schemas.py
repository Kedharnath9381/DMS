from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


ScenarioType = Literal[
    "NORMAL",
    "CPU_CONTENTION",
    "DISK_CONTENTION",
    "COMBINED",
    "COMBINED_CONTENTION"
]


class ExperimentCreate(BaseModel):

    name: str = Field(
        min_length=1,
        max_length=120
    )

    dataset_size_mb: int = Field(
        gt=0,
        le=5000
    )

    scenario: ScenarioType = "NORMAL"

    target_rto_seconds: int = Field(
        gt=0
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        value = value.strip()

        if not value:
            raise ValueError("Experiment name cannot be empty")

        return value


class ExperimentOut(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    dataset_size_mb: int
    scenario: str
    target_rto_seconds: int
    status: str
    backup_duration_seconds: Optional[float]
    restore_duration_seconds: Optional[float]
    integrity_status: str
    rto_status: str
    created_at: datetime