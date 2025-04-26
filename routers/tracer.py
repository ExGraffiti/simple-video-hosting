from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates



router = APIRouter(prefix="", tags=["tracer"])


# Монтируем статические файлы (CSS, JS)
router.mount("/static", StaticFiles(directory="static"), name="static")

# Подключаем шаблоны Jinja2
templates = Jinja2Templates(directory="templates")


# Главная страница
@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Страница просмотра видео
@router.get("/watch/{video_key}", response_class=HTMLResponse)
async def watch_video(request: Request, video_key: str):
    return templates.TemplateResponse("video.html", {"request": request, "video_key": video_key})

