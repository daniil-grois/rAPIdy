# JSON
JSON в документации веб-фреймворка на Python описывает способы работы с данными в формате JSON из тела HTTP-запроса. JSON (JavaScript Object Notation) - это удобный и распространенный формат для передачи структурированных данных между клиентом и сервером. В этом разделе представлены три типа для работы с данными в формате JSON

## Ключевые особенности

JsonEncoder - кто принимает?
На текущий момент это техническое ограничение - будет доработано в будущих обновлениях.

## Аттрибуты

* body_max_size
* json_decoder

## Типы данных

### JsonBody
Тип JsonBody используется для извлечения данных из тела HTTP-запроса в формате JSON. Этот тип удобен, когда требуется получить конкретные данные из JSON-структуры, переданной в запросе. В данном примере извлекается username
<details open>
<summary><code>JsonBody</code></summary>

```Python hl_lines="6"
from rapidy.request_params import JsonBody

@routes.get('/')
async def handler(
        request: web.Request,
        username: Annotated[str, JsonBody],
) -> web.Response:
    return web.json_response({'data': 'success'})
```
</details>

<details>
<summary>Расширенный пример <code>JsonBody</code> с валидацией и вложенными схемами</summary>

```Python hl_lines="9 14 15"
from rapidy.request_params import JsonBody

class UserAddress(BaseModel):
    city: str = Field(min_length=1, max_length=100)
    street: str = Field(min_length=1, max_length=100)

class UserData(BaseModel):
    age: int = Field(ge=18, lt=120)
    address: UserAddress

@routes.get('/')
async def handler(
        request: web.Request,
        username: Annotated[str, JsonBody(min_length=1, max_length=100)],
        userdata: Annotated[UserData, JsonBody(alias='userData')],
) -> web.Response:
    return web.json_response({'data': 'success'})
```
</details>

### JsonBodySchema
Тип JsonBodySchema предназначен для извлечения и валидации структурированных данных из тела HTTP-запроса в формате JSON. Здесь в расширенном примере определена модель BodyData, которая включает в себя параметры username и userdata. userdata содержит вложенную модель UserData, описывающую возраст и адрес пользователя. Таким образом, данный тип обеспечивает валидацию структуры данных и их корректности.
<details open>
<summary><code>JsonBodySchema</code></summary>

```Python hl_lines="5 10"
from pydantic import BaseModel
from rapidy.request_params import JsonBodySchema

class UserData(BaseModel):
    username: str

@routes.get('/')
async def handler(
        request: web.Request,
        user_data: Annotated[UserData, JsonBodySchema],
) -> web.Response:
    return web.json_response({'data': 'success'})
```
</details>

<details>
<summary>Расширенный пример <code>JsonBodySchema</code> с валидацией и вложенными схемами</summary>

```Python hl_lines="19"
from pydantic import BaseModel, Field
from rapidy.request_params import JsonBodySchema

class UserAddress(BaseModel):
    city: str = Field(min_length=1, max_length=100)
    street: str = Field(min_length=1, max_length=100)

class UserData(BaseModel):
    age: int = Field(ge=18, lt=120)
    address: UserAddress

class BodyData(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    userdata: UserData = Field(alias='userData')

@routes.get('/')
async def handler(
        request: web.Request,
        body: Annotated[BodyData, JsonBodySchema],
) -> web.Response:
    return web.json_response({'data': 'success'})
```
</details>

### JsonBodyRaw
Тип JsonBodyRaw используется для извлечения данных из тела HTTP-запроса в формате JSON без какой-либо обработки или валидации. Это удобно, когда требуется получить данные в их исходном виде для последующей обработки или передачи на другой сервер.
<details open>
<summary><code>JsonBodyRaw</code></summary>

```Python hl_lines="7"
from typing import Dict, Any
from rapidy.request_params import JsonBodyRaw

@routes.get('/')
async def handler(
        request: web.Request,
        body: Annotated[Dict[str, Any], JsonBodyRaw],
) -> web.Response:
    return web.json_response({'data': 'success'})
```
</details>

!!! warning "Внимание"
    JsonBodyRaw не использует валидацию pydantic. Все данные содержащиеся в типе извлекаются как есть.
    Подробнее см <a href="#raw">Особенности Raw параметров.
