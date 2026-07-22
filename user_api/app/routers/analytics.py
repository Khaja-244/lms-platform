from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..database import get_db
from ..services import analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview/", response_model=schemas.AnalyticsOverviewOut)
def analytics_overview(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin),
):
    return analytics_service.analytics_overview(db)


@router.get("/monthly/", response_model=list[schemas.MonthlyRevenueOut])
def analytics_monthly(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin),
):
    return analytics_service.monthly_revenue(db)


@router.get("/revenue-by-plan/", response_model=list[schemas.RevenueByPlanOut])
def analytics_revenue_by_plan(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin),
):
    return analytics_service.AnalyticsService.revenue_by_plan(db)
