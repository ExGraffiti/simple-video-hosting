from fastapi import UploadFile, Request, APIRouter, File, HTTPException, Depends
from fastapi.responses import StreamingResponse
from routers.auth import requires_auth, oauth2_scheme

from modules import utils, s3

s3_client = s3.S3Client()

router = APIRouter(prefix="", tags=["files"])


@router.delete("/file")
async def delete_file(file_name):
    """Delete file"""
    try:
        await s3_client.delete_file(file_name)
        return {"Ok": True}
    except:
        return {"Ok": False, "details": "Error with delete this file"}


@router.post("/file")
@requires_auth
async def upload_file(
        video_file: UploadFile = File(...),
        preview_file: UploadFile = File(...),
        token: str = Depends(oauth2_scheme),
        user: dict = None  # Пользователь будет добавлен декоратором
):
    """Upload video and preview files"""
    # Проверяем, что файлы имеют правильные расширения
    if not video_file.filename.endswith(".mp4"):
        raise HTTPException(status_code=400, detail="Video file must be .mp4")
    if not preview_file.filename.endswith(".png"):
        raise HTTPException(status_code=400, detail="Preview file must be .png")

    # Проверяем, что названия файлов совпадают (без расширения)
    video_name = video_file.filename.replace(".mp4", "")
    preview_name = preview_file.filename.replace(".png", "")
    if video_name != preview_name:
        raise HTTPException(status_code=400, detail="Video and preview file names must match")

    # Загружаем видео в S3
    await s3_client.put_file(video_file.filename, video_file.file)

    # Загружаем превью в S3
    await s3_client.put_file(preview_file.filename, preview_file.file)

    return {"Ok": True, "details": "Video and preview uploaded"}


@router.get("/image/{image_name}")
async def get_image(image_name: str, request: Request):
    image_name = image_name + '.png'
    # Получаем размер файла
    file_size = await s3_client.get_file_size(image_name)

    # Обрабатываем заголовок Range
    range_header = request.headers.get("Range")
    if range_header:
        start, end = utils.parse_range_header(range_header, file_size)
    else:
        start, end = 0, file_size - 1

    video_stream = s3_client.stream_file(image_name, start, end)

    return StreamingResponse(
        video_stream,
        media_type="image/png",
        headers={"Content-Disposition": f"inline; filename={image_name}.png"},
    )


@router.get("/files")
async def get_files():
    """Get file names"""
    file_content = await s3_client.get_files_list()
    return {"Ok": True, "file_content": file_content}


@router.get("/video/{video_key}")
async def stream_video(video_key: str, request: Request):
    video_key = video_key + '.mp4'
    # Получаем размер файла
    file_size = await s3_client.get_file_size(video_key)

    # Обрабатываем заголовок Range
    range_header = request.headers.get("Range")
    if range_header:
        start, end = utils.parse_range_header(range_header, file_size)
    else:
        start, end = 0, file_size - 1

    # Получаем поток данных из S3
    video_stream = s3_client.stream_file(video_key, start, end)

    # Устанавливаем заголовки для ответа
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Content-Length": str(end - start + 1),
    }

    # Возвращаем StreamingResponse с правильными заголовками
    return StreamingResponse(
        video_stream,
        media_type="video/mp4",
        headers=headers,
        status_code=206 if range_header else 200,
    )
