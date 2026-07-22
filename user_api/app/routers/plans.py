from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas

router = APIRouter(
    prefix="/plans",
    tags=["Plans"],
)


@router.get(
    "/",
    response_model=list[schemas.PlanOut],
)
def list_plans(
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Plan)
        .filter(models.Plan.is_active == True)
        .all()
    )


@router.get(
    "/{plan_id}",
    response_model=schemas.PlanOut,
)
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
):
    plan = (
        db.query(models.Plan)
        .filter(models.Plan.id == plan_id)
        .first()
    )
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan
