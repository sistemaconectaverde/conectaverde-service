from typing import List, Optional
from uuid import UUID

from ninja import Schema


class LoginIn(Schema):
    email: str
    password: str


class RefreshIn(Schema):
    refresh: str


class ProductionClaim(Schema):
    id: UUID
    name: str
    code: str
    department: Optional[str] = None


class UserOut(Schema):
    id: UUID
    name: str
    email: str
    role: str
    productions: List[ProductionClaim]


class TokenPairOut(Schema):
    access: str
    refresh: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserOut


class AccessTokenOut(Schema):
    access: str
    token_type: str = "Bearer"
    expires_in: int


class ErrorOut(Schema):
    detail: str
