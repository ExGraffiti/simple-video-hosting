from fastapi import HTTPException
import uuid


def generate_unique_filename(user_id: str, original_filename: str) -> str:
    # Генерируем уникальный идентификатор
    unique_id = str(uuid.uuid4())
    # Сохраняем расширение файла
    file_extension = original_filename.split(".")[-1]
    # Формируем уникальное имя
    return f"{user_id}/{unique_id}.{file_extension}"

def parse_range_header(range_header: str, file_size: int) -> tuple[int, int]:
    """Парсит заголовок Range и возвращает начальный и конечный байты."""
    range_type, range_value = range_header.split("=")
    if range_type.strip() != "bytes":
        raise HTTPException(status_code=416, detail="Invalid range type")

    start_str, end_str = range_value.split("-")
    start = int(start_str) if start_str else 0
    end = int(end_str) if end_str else file_size - 1

    if start >= file_size or end >= file_size:
        raise HTTPException(status_code=416, detail="Range not satisfiable")

    return start, end

