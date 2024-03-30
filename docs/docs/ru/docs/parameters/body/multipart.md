# Multipart

## Ключевые особенности

duplicates parse as array - с примерами

Описать что чтобы нормально парсилась форм дата, нужен обязательно заголовок Content-Type - выпустить патч, где больше
необязательно

Укзаать что если заголовка нет поле извлечется как bytearray


Показать работу с файлами

Описать что сохранение файла будет добавлено в одном из следующих обновлений

## Извлечение данных

Описать как происходит извлечение данных из каждой части мультипарт
Как влияет заголовок и тд

## Типы данных

### MultipartBody
<details open>
<summary><code>MultipartBody</code></summary>

```Python hl_lines="6"
from rapidy.request_params import MultipartBody

@routes.get('/')
async def handler(
        request: web.Request,
        username: Annotated[str, MultipartBody],
) -> web.Response:
    return web.json_response({'data': 'success'})
```
</details>

<details>
<summary>Расширенный пример <code>MultipartBody</code> с дополнительной валидацией</summary>

```Python hl_lines="6 7"
from rapidy.request_params import MultipartBody

@routes.get('/')
async def handler(
        request: web.Request,
        username: Annotated[str, MultipartBody(min_length=1, max_length=100)],
        age: Annotated[int, MultipartBody(ge=18, lt=120)],
) -> web.Response:
    return web.json_response({'data': 'success'})
```
</details>

### MultipartBodySchema
<details open>
<summary><code>MultipartBodySchema</code></summary>

```Python hl_lines="10"
from pydantic import BaseModel
from rapidy.request_params import MultipartBodySchema

class UserData(BaseModel):
    username: str

@routes.get('/')
async def handler(
        request: web.Request,
        user_data: Annotated[UserData, MultipartBodySchema],
) -> web.Response:
    return web.json_response({'data': 'success'})
```
</details>

<details open>
<summary>Расширенный пример <code>MultipartBodySchema</code> с дополнительной валидацией</summary>

```Python hl_lines="19"
from pydantic import BaseModel, Field
from rapidy.request_params import MultipartBodySchema

class UserData(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=18, lt=120)

@routes.get('/')
async def handler(
        request: web.Request,
        body: Annotated[UserData, MultipartBodySchema],
) -> web.Response:
    return web.json_response({'data': 'success'})
```
</details>

### MultipartBodyRaw
<details open>
<summary><code>MultipartBodyRaw</code></summary>

```Python hl_lines="7"
from typing import Dict, Any
from rapidy.request_params import MultipartBodyRaw

@routes.get('/')
async def handler(
        request: web.Request,
        body: Annotated[Dict[str, Any], MultipartBodyRaw],
) -> web.Response:
    return web.json_response({'data': 'success'})
```
</details>

<span class="note-color">Внимание!</span><br/>
<i>
    MultipartBodyRaw не использует валидацию pydantic. Все данные содержащиеся в типе извлекаются как есть.
    Подробнее см <a href="#raw">Особенности Raw параметров.</a>
</i>
