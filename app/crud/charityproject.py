from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models import CharityProject


class CRUDCharityProject(CRUDBase):

    async def get_project_by_name(
        self,
        project_name: str,
        session: AsyncSession,
    ) -> Optional[CharityProject]:
        project = await session.execute(
            select(CharityProject).where(
                CharityProject.name == project_name
            )
        )
        return project.scalars().first()

    async def get_projects_by_competion_rate(
        self,
        session: AsyncSession
    ) -> list[dict[str, str]]:
        projects = await session.execute(
            select([CharityProject]).where(CharityProject.fully_invested == 1)
        )
        projects = projects.scalars().all()
        projects_list = sorted(
            [
                {
                    'name': project.name,
                    'duration': project.close_date - project.create_date,
                    'description': project.description
                }
                for project in projects
            ],
            key=lambda x: x['duration']
        )
        return projects_list


charity_project_crud = CRUDCharityProject(CharityProject)
