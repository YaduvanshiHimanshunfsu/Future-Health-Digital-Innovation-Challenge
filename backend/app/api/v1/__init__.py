from fastapi import APIRouter

from app.api.v1 import (
    access_log,
    break_glass,
    cases,
    consents,
    couples,
    health,
    invitations,
    me,
    packs,
    reports,
    results,
    shared,
)

api_v1 = APIRouter()
for module in (
    health,
    packs,
    reports,
    me,
    results,
    access_log,
    consents,
    shared,
    couples,
    invitations,
    cases,
    break_glass,
):
    api_v1.include_router(module.router)
