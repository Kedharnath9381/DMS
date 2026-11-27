from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import StreamingResponse
import csv
import io
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from . import models, schemas
from .backup_engine import run_experiment
from typing import List

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Disaster Recovery RTO Verification API",
    version="0.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "service": "dr-rto-api"
    }


@app.get("/api/experiments", response_model=List[schemas.ExperimentOut])
def list_experiments(db: Session = Depends(get_db)):

    return (
        db.query(models.Experiment)
        .order_by(models.Experiment.created_at.desc())
        .all()
    )


@app.post(
    "/api/experiments",
    response_model=schemas.ExperimentOut,
    status_code=201
)
def create_experiment(
    payload: schemas.ExperimentCreate,
    db: Session = Depends(get_db)
):

    experiment = models.Experiment(**payload.model_dump())

    db.add(experiment)
    db.commit()
    db.refresh(experiment)

    return experiment


@app.post("/api/experiments/run")
def run_experiment_endpoint(
    payload: schemas.ExperimentCreate,
    db: Session = Depends(get_db)
):

    # Create experiment record
    experiment = models.Experiment(
        name=payload.name,
        dataset_size_mb=payload.dataset_size_mb,
        scenario=payload.scenario,
        target_rto_seconds=payload.target_rto_seconds,
        status="RUNNING"
    )

    db.add(experiment)
    db.commit()
    db.refresh(experiment)

    try:

        # Execute real backup and restore experiment
        results = run_experiment(
            dataset_size_mb=payload.dataset_size_mb,
            target_rto_seconds=payload.target_rto_seconds,
            scenario=payload.scenario
        )

        # Update database with measured results
        experiment.backup_duration_seconds = (
            results["backup_duration_seconds"]
        )

        experiment.restore_duration_seconds = (
            results["restore_duration_seconds"]
        )

        experiment.integrity_status = (
            results["integrity_status"]
        )

        experiment.rto_status = (
            results["rto_status"]
        )

        if results["recovery_success"] and results["rto_achieved"]:
            experiment.status = "COMPLETED"
        else:
            experiment.status = "FAILED"

        db.commit()
        db.refresh(experiment)

        return {
            "message": "Experiment completed",
            "experiment": experiment,
            "results": results
        }

    except Exception as e:
        import traceback

        traceback.print_exc()

        experiment.status = "FAILED"

        db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Experiment failed: {str(e)}"
        )


@app.get("/api/experiments/{experiment_id}", response_model=schemas.ExperimentOut)
def get_experiment(
    experiment_id: int,
    db: Session = Depends(get_db)
):

    experiment = (
        db.query(models.Experiment)
        .filter(models.Experiment.id == experiment_id)
        .first()
    )

    if not experiment:

        raise HTTPException(
            status_code=404,
            detail="Experiment not found"
        )

    return experiment
@app.get("/api/experiments/export/csv")
def export_experiments_csv(db: Session = Depends(get_db)):

    experiments = (
        db.query(models.Experiment)
        .filter(models.Experiment.status.in_(["COMPLETED", "FAILED"]))
        .order_by(models.Experiment.created_at.asc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)

    # CSV header
    writer.writerow([
        "Experiment ID",
        "Experiment Name",
        "Dataset Size (MiB)",
        "Scenario",
        "Target RTO (seconds)",
        "Backup Duration (seconds)",
        "Restore Duration (seconds)",
        "Integrity Status",
        "RTO Status",
        "Experiment Status",
        "Created At"
    ])

    # Experiment records
    for experiment in experiments:
        writer.writerow([
            experiment.id,
            experiment.name,
            experiment.dataset_size_mb,
            experiment.scenario,
            experiment.target_rto_seconds,
            experiment.backup_duration_seconds,
            experiment.restore_duration_seconds,
            experiment.integrity_status,
            experiment.rto_status,
            experiment.status,
            experiment.created_at
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=experiment_results.csv"
        }
    )