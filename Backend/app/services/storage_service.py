import logging
from supabase import Client
from typing import List

logger = logging.getLogger(__name__)


class StorageUploadError(Exception):
    pass


def upload_file(
    supabase: Client,
    bucket: str,
    path: str,
    file_bytes: bytes,
    content_type: str,
) -> str:
    supabase.storage.from_(bucket).upload(
        path=path,
        file=file_bytes,
        file_options={"content-type": content_type, "upsert": "true"},
    )
    public_url = supabase.storage.from_(bucket).get_public_url(path)
    if not public_url:
        raise StorageUploadError(f"Failed to get public URL for {path}")
    return public_url


def delete_file(supabase: Client, bucket: str, path: str) -> None:
    supabase.storage.from_(bucket).remove([path])


def delete_files(supabase: Client, bucket: str, paths: List[str]) -> None:
    if paths:
        supabase.storage.from_(bucket).remove(paths)
