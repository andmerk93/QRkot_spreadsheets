from aiogoogle import Aiogoogle, AiogoogleError
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_session
from app.core.google_client import get_service
from app.core.user import current_superuser
from app.core.config import settings

from app.crud.charityproject import charity_project_crud
from app.services.google_api import (
    generate_table,
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
    google_service: Aiogoogle = Depends(get_service)
):
    projects = await charity_project_crud.get_projects_by_completion_rate(
        session)
    table_values, rows, columns = generate_table(projects)
    try:
        spreadsheet_id, spreadsheet_url = await spreadsheets_create(
            google_service, rows, columns
        )
    except AiogoogleError as error:
        raise HTTPException(500, error)
    await set_user_permissions(google_service, spreadsheet_id, settings.email)
    await spreadsheets_update_value(
        google_service, spreadsheet_id, table_values, rows, columns
    )
    return dict(doc=spreadsheet_url)
