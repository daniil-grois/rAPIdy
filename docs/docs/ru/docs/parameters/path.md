# Path parameters
Path параметры позволяют вашему веб-приложению создавать динамические маршруты, которые могут изменяться в зависимости от входящего запроса. Эти параметры включаются в адресную строку URL и используются для передачи переменных данных в ваше приложение. Например, вы можете использовать path параметры для идентификации определенного ресурса или объекта.

Для определения path параметров используются placeholder'ы в URL. Например, если вы хотите создать маршрут для отображения информации о конкретном пользователе, вы можете использовать следующий синтаксис:

`/users/{user_id}`

Здесь `{user_id}` будет представлять собой динамический параметр, который вы можете использовать в вашем коде для обработки запросов.


!!! example ""
    ```Python hl_lines="1"
    @routes.get('/{user_id}')
    async def handler(...) -> web.Response:
        ...
    ```
    
    ```Python hl_lines="4"
    async def handler(...) -> web.Response:
        ...
    
    route = web.get('/{user_id}', handler)
    ```
    !!! tip "Примеры обработчиков для каждого типа данных [<code>Path</code>](#path) [<code>PathSchema</code>](#pathschema) [<code>PathRaw</code>](#pathraw)"
    
___
## Типы данных
### Path
!!! tip "Рекомендованный параметр для этого типа данных"

Тип Path используется для извлечения конкретных данных из пути URL запроса. Этот тип подходит, когда вы знаете точную структуру URL и хотите извлечь определенные значения, такие как идентификатор пользователя, имя ресурса и т.д.

!!! example "Первый способ"
    ```Python hl_lines="7 10"
    {!> ./parameters/path/types/Path/ex_01.py !}
    ```
    ??? tip "Пример запроса"
        Скопируйте пример в файл `main.py` и запустите `python3 main.py`.<br/>
        В браузере перейдите по адресу: <a href="http://127.0.0.1:8080/user_1" target="blank">http://127.0.0.1:8080/user_1</a>
        или отправьте запрос с помощью `curl`:
        ```
        curl -X GET http://127.0.0.1:8080/user_1
        ```
        вы получите ответ:
        ```
        {"user_id": "user_1"}
        ```

??? example "Несколько параметров <code>Path</code>"
    ```Python hl_lines="7 10 11"
    {!> ./parameters/path/types/Path/ex_02.py !}
    ```
    ??? tip "Пример запроса"
        Скопируйте пример в файл `main.py` и запустите `python3 main.py`.<br/>
        В браузере перейдите по адресу:  <a href="http://127.0.0.1:8080/user_1/param_2" target="blank">http://127.0.0.1:8080/user_1/param_2</a>
        или отправьте запрос с помощью `curl`:
        ```
        curl -X GET http://127.0.0.1:8080/user_1/param_2
        ```
        вы получите ответ:
        ```
        {"user_id": "user_1", "some_param", "param_2"}
        ```


### PathSchema
Тип PathSchema предназначен для извлечения и валидации структурированных данных из пути URL запроса. Он удобен, когда вам нужно извлечь большое количество данных из URL и обеспечить их корректность и целостность, например, идентификаторы пользователя, даты, имена файлов и т.д.

!!! tip ""
    Маловероятно, что вы будете использовать этот тип по причине того, что в Path обычно передаются не более 1-2 параметров, но для 
    единообразия данный тип существует.

!!! example "<code>PathSchema</code>"
    ```Python hl_lines="9 11 14"
    {!> ./parameters/path/types/PathSchema/ex_01.py !}
    ```
    ??? tip "Пример запроса"
        Скопируйте пример в файл `main.py` и запустите `python3 main.py`.<br/>
        В браузере перейдите по адресу: <a href="http://127.0.0.1:8080/user_1" target="blank">http://127.0.0.1:8080/user_1</a>
        или отправьте запрос с помощью `curl`:
        ```
        curl -X GET http://127.0.0.1:8080/user_1
        ```
        вы получите ответ:
        ```
        {"user_id": "user_1"}
        ```

??? example "<code>PathSchema</code> с несколькими параметрами"
    ```Python hl_lines="9 10 12 15"
    {!> ./parameters/path/types/PathSchema/ex_02.py !}
    ```
    ??? tip "Пример запроса"
        Скопируйте пример в файл `main.py` и запустите `python3 main.py`.<br/>
        В браузере перейдите по адресу:  <a href="http://127.0.0.1:8080/user_1/param_2" target="blank">http://127.0.0.1:8080/user_1/param_2</a>
        или отправьте запрос с помощью `curl`:
        ```
        curl -X GET http://127.0.0.1:8080/user_1/param_2
        ```
        вы получите ответ:
        ```
        {"user_id": "user_1", "some_param", "param_2"}
        ```

### PathRaw
Тип PathRaw используется для извлечения необработанных данных из пути URL запроса без какой-либо дополнительной обработки или валидации. Это полезно, когда вам нужно получить данные в их исходном виде, например, для обработки специальных символов или шаблонов.

!!! example "<code>PathRaw</code>"
    ```Python hl_lines="8 11"
    {!> ./parameters/path/types/PathRaw/ex_01.py !}
    ```
    ??? tip "Пример запроса"
        Скопируйте пример в файл `main.py` и запустите `python3 main.py`.<br/>
        В браузере перейдите по адресу: <a href="http://127.0.0.1:8080/user_1" target="blank">http://127.0.0.1:8080/user_1</a>
        или отправьте запрос с помощью `curl`:
        ```
        curl -X GET http://127.0.0.1:8080/user_1
        ```
        вы получите ответ:
        ```
        {"path": {"user_id": "user_1"}}
        ```

??? example "PathRaw с несколькими параметрами"
    ```Python hl_lines="8 11"
    {!> ./parameters/path/types/PathRaw/ex_02.py !}
    ```
    ??? tip "Пример запроса"
        Скопируйте пример в файл `main.py` и запустите `python3 main.py`.<br/>
        В браузере перейдите по адресу: <a href="http://127.0.0.1:8080/user_1/param_2" target="blank">http://127.0.0.1:8080/user_1/param_2</a>
        или отправьте запрос с помощью `curl`:
        ```
        curl -X GET http://127.0.0.1:8080/user_1/param_2
        ```
        вы получите ответ:
        ```
        {"path": {"user_id": "user_1", "some_param": "param_2"}}
        ```

!!! warning "Внимание"
    PathRaw не использует валидацию pydantic. Все данные содержащиеся в типе извлекаются как есть.
    Подробнее см. в разделе [Raw data](../raw_data.md).
___
## Ключевые особенности
### Поддержка регулярных выражений
Переменные пути имеют поддержку регулярных выражений
<i>(источник: <a href="https://docs.aiohttp.org/en/stable/web_quickstart.html" target="blank">aiohttp quickstart</a> раздел <b><span class="note-color">Resources and Routes</span></b>).</i>

По умолчанию каждый параметр пути соответствует регулярному выражению `[^{}/]+`.

Вы также можете указать собственное регулярное выражение в форме `{<path_variable>:<regex>}`.

!!! example ""
    ```Python hl_lines="1"
    @routes.get('/{user_id:\d+}')
    async def handler(...) -> web.Response:
        ...
    ```

    ```Python hl_lines="4"
    async def handler(...) -> web.Response:
        ...

    route = web.get(r'/{name:\d+}', handler
    ```

### Использование именованных ресурсов
!!! tip "Подробнее о именованных ресурсах [Named resources](../named_resources.md)"

!!! example "Пример перенаправления с предопределенным <code>Path-параметром</code>"
    ```python hl_lines="7 17 18"
    {!> ./parameters/path/named_resource/ex_01.py !}
    ```
    ??? tip "Пример запроса"
        Скопируйте пример в файл `main.py` и запустите `python3 main.py`.<br/>
        В браузере если вы перейдите по адресу: <a href="http://127.0.0.1:8080" target="blank">http://127.0.0.1:8080</a>, то вас перенаправит на
        ```
        http://127.0.0.1:8080/get_user_info/user_1
        ```
        вы получите ответ:
        ```
        {"path": {"user_id": "user_1", "some_param": "param_2"}}
        ```

### Значения по умолчанию
Поскольку Path-параметр является составной частью пути, он обязателен для указания и не может быть заменен значением по умолчанию.
!!! warning "Если при запуске сервера будет использоваться значение по умолчанию для любого Path-параметра, это приведет к возникновению исключения"


#### Попытка задать значение по умолчанию для <code>Path</code>
!!! example ""
    ```python hl_lines="4"
    @routes.get('/{user_id}')
    async def handler(
            request: web.Request,
            user_id: Annotated[str, Path] = 'user_1',
    ) ->  web.Response:
    ```
#### Попытка задать значение по умолчанию для <code>PathSchema</code>
!!! example ""
    ```python hl_lines="7"
    class PathRequestSchema(BaseModel):
        user_id: str

    @routes.get('/{user_id}')
    async def handler(
            request: web.Request,
            path: Annotated[PathRequestSchema, PathSchema] = PathRequestSchema(user_id='user_1'),
    ) -> web.Response:
    ```
#### Попытка задать значение по умолчанию для <code>PathRaw</code>
!!! example ""
    ```python hl_lines="4"
    @routes.get('/{user_id}')
    async def handler(
            request: web.Request,
            path: Annotated[PathRequestSchema, PathSchema] = {'user_id': 'user_1'},
    ) -> web.Response:
    ```

    ```python
    AssertionError: Handler attribute with Type `Path` cannot have a default value.
    Handler path: `<path to file>/main.py`.
    Handler name: `handler`.
    Attribute name: `user_id`.
    ```

!!! warning "Внимание"
    Для `PathRequestSchema` есть вариант передать значение по умолчанию, через `pydantic.Field`.<br/>
    К сожалению, в виду технических ограничений, этот сценарий не вызовет исключения, поэтому он просто игнорируется.

    ```python hl_lines="2 7"
    class PathRequestSchema(BaseModel):
        user_id: str = Field('user_1')

    @routes.get('/{user_id}')
    async def handler(
            request: web.Request,
            path: Annotated[PathRequestSchema, PathSchema],
    ) -> web.Response:
        return web.json_response({'user_id': path.user_id})
    ```
    
    Если у вас запущен сервер по адресу `http://127.0.0.1:8080` и вы перейдете по <a href="http://127.0.0.1:8080/" target="blank">http://127.0.0.1:8080/</a>, то получите в ответе `404: Not Found`.


!!! tip ""
    Подробнее о значениях по умолчанию см в разделе [Default values](../default_values.md)