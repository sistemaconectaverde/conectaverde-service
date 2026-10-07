from datetime import date
from typing import Optional

from ninja import ModelSchema, Schema

from apps.productions.models import Production


class ProductionOut(ModelSchema):
    class Meta:
        model = Production
        fields = [
            "id",
            "name",
            "code",
            "client_name",
            "location",
            "city",
            "state",
            "episodes_count",
            "shooting_days",
            "pre_production_days",
            "post_production_days",
            "start_date",
            "end_date",
            "status",
            "created_at",
            "updated_at",
        ]


class ProductionIn(Schema):
    name: str
    code: str
    client_name: str = ""
    location: str = ""
    city: str = ""
    state: str = ""
    episodes_count: Optional[int] = None
    shooting_days: Optional[int] = None
    pre_production_days: Optional[int] = None
    post_production_days: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Production.Status = Production.Status.PLANEJADA


class ProductionFilters(Schema):
    status: Optional[Production.Status] = None
    q: Optional[str] = None

