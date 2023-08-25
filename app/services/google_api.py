from datetime import datetime as dt

from aiogoogle import Aiogoogle


def now_time():
    return dt.now().strftime('%Y/%m/%d %H:%M:%S')


async def spreadsheets_create(google_service: Aiogoogle) -> str:
    service = await google_service.discover('sheets', 'v4')
    spreadsheet_body = dict(
        # Свойства документа
        properties=dict(
            title=f'Отчёт от {now_time()}',
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
    response = await google_service.as_service_account(
        service.spreadsheets.create(json=spreadsheet_body)
    )
    spread_sheet_id = response['spreadsheetId']
    return spread_sheet_id


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


async def spreadsheets_update_value(
        google_service: Aiogoogle,
        spreadsheet_id: str,
        projects: list,
) -> None:
    service = await google_service.discover('sheets', 'v4')
    table_values = [
        ['Отчёт от', now_time()],
        ['Топ проектов по скорости закрытия'],
        ['Название проекта', 'Время сбора', 'Описание'],
        *[
            [project['name'], str(project['duration']), project['description']]
            for project in projects
        ]
    ]
    request_body = dict(
        majorDimension='ROWS',
        values=table_values
    )
    await google_service.as_service_account(
        service.spreadsheets.values.update(
            spreadsheetId=spreadsheet_id,
            range=f'R1C1:R{len(table_values)}C3',
            valueInputOption='USER_ENTERED',
            json=request_body
        )
    )
