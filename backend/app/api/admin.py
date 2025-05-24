from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.api.auth import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.models.drone import Drone
from app.models.flight_request import FlightRequest, FlightStatus
from app.models.telemetry import Telemetry 
from app.models.violation import Violation, ViolationType
from app.models.no_fly_zone import NoFlyZone

router = APIRouter()


@router.get("/metrics/overview")
def get_overview_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get overview metrics for the admin dashboard."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Get user count
    user_count = db.query(func.count(User.id)).scalar()
    
    # Get drone count
    drone_count = db.query(func.count(Drone.id)).scalar()
    
    # Get flight request counts
    total_flights = db.query(func.count(FlightRequest.id)).scalar()
    pending_flights = db.query(func.count(FlightRequest.id)).filter(FlightRequest.status == FlightStatus.PENDING).scalar()
    approved_flights = db.query(func.count(FlightRequest.id)).filter(FlightRequest.status == FlightStatus.APPROVED).scalar()
    rejected_flights = db.query(func.count(FlightRequest.id)).filter(FlightRequest.status == FlightStatus.REJECTED).scalar()
    
    # Get violation count
    violation_count = db.query(func.count(Violation.id)).scalar()
    
    # Get no-fly zone count
    no_fly_zone_count = db.query(func.count(NoFlyZone.id)).scalar()
    
    return {
        "user_count": user_count,
        "drone_count": drone_count,
        "flights": {
            "total": total_flights,
            "pending": pending_flights,
            "approved": approved_flights,
            "rejected": rejected_flights,
        },
        "violation_count": violation_count,
        "no_fly_zone_count": no_fly_zone_count,
    }


@router.get("/metrics/recent-activity")
def get_recent_activity(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get metrics about recent activity."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Calculate start date
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get recent flight requests
    recent_flight_requests = (
        db.query(FlightRequest)
        .filter(FlightRequest.created_at >= start_date)
        .order_by(FlightRequest.created_at.desc())
        .limit(10)
        .all()
    )
    
    # Get recent violations
    recent_violations = (
        db.query(Violation)
        .filter(Violation.timestamp >= start_date)
        .order_by(Violation.timestamp.desc())
        .limit(10)
        .all()
    )
    
    # Get recent user registrations
    recent_users = (
        db.query(User)
        .filter(User.created_at >= start_date)
        .order_by(User.created_at.desc())
        .limit(5)
        .all()
    )
    
    # Format the results to include only necessary fields
    formatted_flight_requests = [
        {
            "id": str(fr.id),
            "drone_id": str(fr.drone_id),
            "status": fr.status.value,
            "created_at": fr.created_at.isoformat(),
        }
        for fr in recent_flight_requests
    ]
    
    formatted_violations = [
        {
            "id": str(v.id),
            "drone_id": str(v.drone_id),
            "type": v.type.value,
            "timestamp": v.timestamp.isoformat(),
            "description": v.description,
        }
        for v in recent_violations
    ]
    
    formatted_users = [
        {
            "id": str(u.id),
            "email": u.email,
            "name": f"{u.first_name} {u.last_name}",
            "created_at": u.created_at.isoformat(),
        }
        for u in recent_users
    ]
    
    return {
        "recent_flight_requests": formatted_flight_requests,
        "recent_violations": formatted_violations,
        "recent_users": formatted_users,
    }


@router.get("/metrics/flights-over-time")
def get_flights_over_time(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get metrics about flight requests over time."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Calculate start date
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Initialize daily counts
    daily_counts = {}
    for i in range(days):
        date = (datetime.utcnow() - timedelta(days=i)).date()
        daily_counts[date.isoformat()] = {
            "total": 0,
            "approved": 0,
            "rejected": 0,
            "pending": 0,
        }
    
    # Get flight requests in the date range
    flight_requests = (
        db.query(FlightRequest)
        .filter(FlightRequest.created_at >= start_date)
        .all()
    )
    
    # Count flights by day and status
    for fr in flight_requests:
        date = fr.created_at.date().isoformat()
        if date in daily_counts:
            daily_counts[date]["total"] += 1
            if fr.status == FlightStatus.APPROVED:
                daily_counts[date]["approved"] += 1
            elif fr.status == FlightStatus.REJECTED:
                daily_counts[date]["rejected"] += 1
            elif fr.status == FlightStatus.PENDING:
                daily_counts[date]["pending"] += 1
    
    # Format the results as a list for easier consumption by charting libraries
    result = [
        {
            "date": date,
            "total": data["total"],
            "approved": data["approved"],
            "rejected": data["rejected"],
            "pending": data["pending"],
        }
        for date, data in daily_counts.items()
    ]
    
    # Sort by date ascending
    result.sort(key=lambda x: x["date"])
    
    return result


@router.get("/metrics/violations-by-type")
def get_violations_by_type(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get metrics about violations by type."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Calculate start date
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Initialize counts
    violation_counts = {vtype.value: 0 for vtype in ViolationType}
    
    # Get violations in the date range
    violations = (
        db.query(Violation)
        .filter(Violation.timestamp >= start_date)
        .all()
    )
    
    # Count violations by type
    for v in violations:
        violation_counts[v.type.value] += 1
    
    # Format the results as a list for easier consumption by charting libraries
    result = [
        {
            "type": vtype,
            "count": count,
        }
        for vtype, count in violation_counts.items()
    ]
    
    return result


@router.get("/metrics/active-drones")
def get_active_drones(
    hours: int = 24,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get metrics about active drones in the given time period."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Calculate start date
    start_date = datetime.utcnow() - timedelta(hours=hours)
    
    # Get active drones based on telemetry
    active_drone_ids = (
        db.query(Telemetry.drone_id)
        .filter(Telemetry.timestamp >= start_date)
        .distinct()
        .all()
    )
    
    active_drone_ids = [str(drone_id[0]) for drone_id in active_drone_ids]
    
    # Get info for active drones
    active_drones = (
        db.query(Drone)
        .filter(Drone.id.in_(active_drone_ids))
        .all()
    )
    
    # Format the results
    formatted_drones = [
        {
            "id": str(drone.id),
            "model": drone.model,
            "serial_number": drone.serial_number,
            "user_id": str(drone.user_id),
        }
        for drone in active_drones
    ]
    
    return {
        "count": len(formatted_drones),
        "drones": formatted_drones,
    } 