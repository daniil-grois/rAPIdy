# Cookie parameters
Cookie параметры используются для передачи информации между клиентом и сервером в виде cookie. Эти параметры часто используются для хранения состояния пользователя, такого как идентификаторы сеансов, предпочтения пользователей и другие данные.
___
## Типы данных
### Cookie
Тип Cookie используется для точечного извлечения данных из cookie запроса. Этот тип параметра позволяет получить конкретные значения cookie, передаваемые клиентом в заголовке запроса.
!!! example "Cookie"
    ```Python hl_lines="10 11"
    {!> ./parameters/cookie/types/Cookie/ex_01.py !}
    ```
    ??? tip "Пример запроса"
        Скопируйте пример в файл `main.py` и запустите `python3 main.py`.<br/>
        Отправьте запрос с помощью `curl`:
        ```
        curl -X GET --cookie "userId=user_1;userSession=awesome_session" http://127.0.0.1:8080
        ```
        вы получите ответ:
        ```
        {"user_id": "user_1", "user_session": "awesome_session"}
        ```

### CookieSchema
CookieSchema используется для извлечения и валидации структурированных данных из cookie запроса. Этот тип удобен, когда требуется извлечь несколько значений cookie и обеспечить их правильность и целостность.
!!! example "CookieSchema"
    ```Python hl_lines="9 10 15"
    {!> ./parameters/cookie/types/CookieSchema/ex_01.py !}
    ```
    ??? tip "Пример запроса"
        Скопируйте пример в файл `main.py` и запустите `python3 main.py`.<br/>
        Отправьте запрос с помощью `curl`:
        ```
        curl -X GET --cookie "userId=user_1;userSession=awesome_session" http://127.0.0.1:8080
        ```
        вы получите ответ:
        ```
        {"user_id": "user_1", "user_session": "awesome_session"}
        ```

### CookieRaw
!!! example "CookieRaw"
    ```Python hl_lines="11"
    {!> ./parameters/cookie/types/CookieRaw/ex_01.py !}
    ```
    ??? tip "Пример запроса"
        Скопируйте пример в файл `main.py` и запустите `python3 main.py`.<br/>
        Отправьте запрос с помощью `curl`:
        ```
        curl -X GET --cookie "userId=user_1;userSession=awesome_session" http://127.0.0.1:8080
        ```
        вы получите ответ:
        ```
        {"cookies": {userId": "user_1", "userSession": "awesome_session"}}
        ```

!!! warning "Внимание"
    CookieRaw не использует валидацию pydantic. Все данные содержащиеся в типе извлекаются как есть.
    Подробнее см <a href="#raw">Особенности Raw параметров.</a>
