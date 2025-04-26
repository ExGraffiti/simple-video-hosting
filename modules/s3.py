import asyncio
from contextlib import asynccontextmanager
from aiobotocore.session import get_session
import hashlib
import cfg

class S3Client:
    def __init__(self):
        self.config = {
            "aws_access_key_id": cfg.s3cfg['access_key'],
            "aws_secret_access_key": cfg.s3cfg['secret_key'],
            "endpoint_url": cfg.s3cfg['endpoint_url'],
        }
        self.bucket_name = cfg.s3cfg['bucket_name']
        self.session = get_session()

    @asynccontextmanager
    async def get_client(self):
        async with self.session.create_client("s3", **self.config) as client:
            yield client

    """Сохранить файл"""
    async def put_file(self, filename: str, file):
        async with self.get_client() as client:
            file_hash = hashlib.sha256(file.read()).hexdigest()
            file.seek(0)  # Переместить курсор в начало файла
            await client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=file,
                ChecksumSHA256=file_hash,
            )

    """Получить файл (Не универсальный запрос)"""
    async def get_file(self, object_name: str, ):
        async with self.get_client() as client:
            response = await client.get_object(Bucket=self.bucket_name, Key=object_name)
            content = await response['Body'].read()
            return content

    """Удалить файл"""
    async def delete_file(self, object_name: str, ):
        async with self.get_client() as client:
            await client.delete_object(Bucket=self.bucket_name, Key=object_name)

    """Получить список файлов"""
    async def get_files_list(self):
        async with self.get_client() as client:
            response = await client.list_objects_v2(Bucket=self.bucket_name)
            files_list = [obj['Key'].replace('.mp4', '') for obj in response['Contents'] if 'mp4' in obj['Key']]
            return files_list

    """Стриминг файлов"""
    async def get_file_size(self, object_name: str) -> int:
        async with self.get_client() as client:
            response = await client.head_object(Bucket=self.bucket_name, Key=object_name)
            return response['ContentLength']

    async def stream_file(self, object_name: str, start: int = 0, end: int = None):
        async with self.get_client() as client:
            range_header = f"bytes={start}-{end}" if end else f"bytes={start}-"
            response = await client.get_object(
                Bucket=self.bucket_name,
                Key=object_name,
                Range=range_header
            )
            async for chunk in response['Body'].iter_chunks():
                yield chunk
    """/"""



async def main():
    s3_client = S3Client()

    files_list = await s3_client.get_files_list()
    print(files_list)


if __name__ == '__main__':
    asyncio.run(main())
