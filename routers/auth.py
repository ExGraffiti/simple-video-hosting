from fastapi import Depends, HTTPException, status, APIRouter, Header
from fastapi.security import OAuth2AuthorizationCodeBearer
from fastapi.responses import RedirectResponse
from google.oauth2 import id_token
import requests as http_requests
from google.auth.transport import requests as google_requests
from google.auth.exceptions import GoogleAuthError
from modules import storage
import cfg
from functools import wraps



router = APIRouter(prefix="", tags=["auth"])

CLIENT_ID = cfg.googleAuth['CLIENT_ID']
CLIENT_SECRET = cfg.googleAuth['CLIENT_SECRET']
REDIRECT_URI = cfg.googleAuth['REDIRECT_URI']





oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://accounts.google.com/o/oauth2/auth",
    tokenUrl="https://accounts.google.com/o/oauth2/token",
    scopes={"openid": "OpenID connect", "email": "Access to your email", "profile": "Access to your profile"},
)

storage = storage.Storage()

def get_db():
    """Зависимость для получения курсора базы данных."""
    try:
        cursor = storage.get_cursor()
        yield cursor
    finally:
        cursor.close()

@router.get("/login")
async def login():
    return RedirectResponse(
        f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=openid%20email%20profile"
    )

@router.get("/auth/callback")
async def auth_callback(code: str, cursor=Depends(get_db)):
    try:
        # Обмен кода авторизации на токен доступа
        token_response = http_requests.post(
            "https://accounts.google.com/o/oauth2/token",
            data={
                "code": code,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        token_response.raise_for_status()
        token_data = token_response.json()

        # Верификация токена
        idinfo = id_token.verify_oauth2_token(token_data["id_token"], google_requests.Request(), CLIENT_ID, clock_skew_in_seconds=60)



        # Проверка, что токен был выдан для нашего клиента
        if idinfo["aud"] != CLIENT_ID:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token audience")

        # Поиск пользователя в базе данных по google_id
        cursor.execute("SELECT * FROM users WHERE google_id = %s", (idinfo["sub"],))
        user = cursor.fetchone()

        if not user:
            # Создание нового пользователя, если он не существует
            cursor.execute(
                "INSERT INTO users (google_id, email, name, access_token) VALUES (%s, %s, %s, %s)",
                (idinfo["sub"], idinfo["email"], idinfo.get("name", ""), token_data["access_token"]),
            )
            storage.connection.commit()
            user_id = cursor.lastrowid
        else:
            # Обновление данных пользователя, если он уже существует
            cursor.execute(
                "UPDATE users SET email = %s, access_token = %s WHERE google_id = %s",
                (idinfo["email"], token_data["access_token"], idinfo["sub"]),
            )
            storage.connection.commit()
            user_id = user[0]  # Предполагаем, что первый столбец — это ID пользователя


        # Перенаправляем пользователя на фронтенд с токеном в URL
        return RedirectResponse(
            url=f"http://localhost:8000/?access_token={token_data['access_token']}&email={idinfo['email']}&name={idinfo.get('name', '')}"
        )

    except GoogleAuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/protected")
async def protected_route(
    authorization: str = Header(None),  # Получаем токен из заголовка Authorization
    cursor=Depends(get_db),
):
    print(authorization)

    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        # Извлекаем токен из заголовка
        if 'Bearer' in authorization:
            token = authorization.split("Bearer ")[1]
        else:
            token = authorization

        # Поиск пользователя по токену в базе данных
        cursor.execute("SELECT * FROM users WHERE access_token = %s", (token,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Возвращаем информацию о пользователе
        return {"email": user[2], "name": user[3], "id": user[0]}  # Предполагаем, что email и name находятся в индексах 2 и 3

    except Exception as e:
        import traceback
        print(str(traceback.format_exc()))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))



def requires_auth(func):
    """Декоратор для проверки авторизации"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        token = kwargs.get("token")
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

        try:
            # Верифицируем токен через Google
            idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), CLIENT_ID)

            # Проверяем, что токен содержит email
            if "email" not in idinfo:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

            # Добавляем информацию о пользователе в kwargs
            kwargs["user"] = idinfo
            return await func(*args, **kwargs)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return wrapper
