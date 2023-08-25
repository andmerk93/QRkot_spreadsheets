from aiogoogle import Aiogoogle
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_session
from app.core.google_client import get_google_service
from app.core.user import current_superuser
from app.core.config import settings

from app.crud.charityproject import charity_project_crud
from app.services.google_api import (
    set_user_permissions,
    spreadsheets_create,
    spreadsheets_update_value
)

router = APIRouter()


@router.get(
    '/',
    response_model=dict[str, str],
    dependencies=[Depends(current_superuser)]
)
async def get_report(
    session: AsyncSession = Depends(get_async_session),
    google_service: Aiogoogle = Depends(get_google_service)
):
    projects = await charity_project_crud.get_projects_by_competion_rate(session) # noqa
    spreadsheet_id = await spreadsheets_create(google_service)
    await set_user_permissions(google_service, spreadsheet_id, settings.email)
    await spreadsheets_update_value(google_service, spreadsheet_id, projects)
    return {'doc': 'https://docs.google.com/spreadsheets/d/' + spreadsheet_id}
