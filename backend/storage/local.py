import os
from backend.storage.base import StorageClient
from backend.config import settings


class LocalStorageClient(StorageClient):
    async def save(self, path: str, data: bytes) -> str:
        full_path = os.path.join(settings.storage_path, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(data)
        return full_path

    async def delete(self, path: str) -> None:
        if os.path.exists(path):
            os.remove(path)


storage = LocalStorageClient()
