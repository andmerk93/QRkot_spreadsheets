from copy import deepcopy
from datetime import datetime as dt

from pydantic import ValidationError

from aiogoogle import Aiogoogle


TABLE_HEADER = (
    ['Топ проектов по скорости закрытия'],
    ['Название проекта', 'Время сбора', 'Описание'],
)

TABLE_PROPERTIES = dict(
    # Свойства документа
    properties=dict(
        title='Актуальный отчёт',
        locale='ru_RU'
    ),
    # Свойства листов документа
    sheets=[dict(
        properties=dict(
            sheetType='GRID',
            sheetId=0,
            title='Sheet',
            gridProperties=dict(
                rowCount=100,
                columnCount=3
            )
        )
    )]
)


def title_with_time():
    return f'Отчёт от {dt.now().strftime("%Y/%m/%d %H:%M:%S")}'


async def spreadsheets_create(
    google_service: Aiogoogle,
    rows: int = 100,
    columns: int = 3,
) -> str:
    check_table_size(rows, columns)
    service = await google_service.discover('sheets', 'v4')
    spreadsheet_body = deepcopy(TABLE_PROPERTIES)
    spreadsheet_body['properties']['title'] = title_with_time()
    properties = spreadsheet_body['sheets'][0]['properties']['gridProperties']
    properties['rowCount'] = rows
    properties['columnCount'] = columns
    response = await google_service.as_service_account(
        service.spreadsheets.create(json=spreadsheet_body)
    )
    return response['spreadsheetId'], response['spreadsheetUrl']


async def set_user_permissions(
    google_service: Aiogoogle,
    spreadsheet_id: str,
    email: str,
) -> None:
    permissions_body = dict(
        type='user',
        role='writer',
        emailAddress=email,
    )
    service = await google_service.discover('drive', 'v3')
    await google_service.as_service_account(
        service.permissions.create(
            fileId=spreadsheet_id,
            json=permissions_body,
            fields='id'
        ))


def sort_projects_by_duration(projects):
    return sorted(
        [
            (
                project.name,
                (project.close_date - project.create_date),
                project.description,
            )
            for project in projects
        ],
        key=lambda x: x[1]  # sort by duration
    )


def stringify_duration(input_tuple):
    name, duration, description = input_tuple
    return name, str(duration), description


def generate_table(projects):
    projects = sort_projects_by_duration(projects)
    table_values = [
        [title_with_time()],
        *TABLE_HEADER,
        *map(stringify_duration, projects)
    ]
    rows = len(table_values)
    columns = max(map(len, table_values))
    return table_values, rows, columns


def check_table_size(rows: int, columns: int):
    if columns > 18278 or rows * columns > 5000000:
        raise ValidationError(
            f'Невозможно создать таблицу размера {rows} x {columns}. '
            'Google-таблицы могут содержать не больше 18278 столбцов '
            'и не больше 5000000 ячеек суммарно '
        )


async def spreadsheets_update_value(
        google_service: Aiogoogle,
        spreadsheet_id: str,
        table_values: list,
        rows: int,
        columns: int,
) -> None:
    service = await google_service.discover('sheets', 'v4')
    await google_service.as_service_account(
        service.spreadsheets.values.update(
            spreadsheetId=spreadsheet_id,
            range=f'R1C1:R{rows}C{columns}',
            valueInputOption='USER_ENTERED',
            json=dict(
                majorDimension='ROWS',
                values=table_values
            )
        )
    )
