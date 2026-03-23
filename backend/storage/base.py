from abc import ABC, abstractmethod


class StorageClient(ABC):
    @abstractmethod
    async def save(self, path: str, data: bytes) -> str:
        """Save data and return the stored path."""

    @abstractmethod
    async def delete(self, path: str) -> None:
        pass
