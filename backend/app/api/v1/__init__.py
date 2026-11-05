from fastapi import APIRouter

from app.api.v1 import (
    access_log,
    break_glass,
    cases,
    chat,
    consents,
    couples,
    health,
    invitations,
    me,
    options,
    packs,
    reports,
    results,
    shared,
    values,
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
    chat,
    options,
    values,
):
    api_v1.include_router(module.router)
