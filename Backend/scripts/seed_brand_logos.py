import os
import sys
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from supabase import create_client
from app.config import settings


async def seed_brand_logos():
    logos_dir = os.path.join(os.path.dirname(__file__), "..", "..", "Frontend", "public", "brand_logos")

    if not os.path.isdir(logos_dir):
        print(f"Brand logos directory not found: {logos_dir}")
        return

    supabase = create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
    )

    files = [f for f in os.listdir(logos_dir) if f.endswith((".png", ".jpg", ".jpeg", ".webp"))]
    print(f"Found {len(files)} brand logo files")

    for filename in sorted(files):
        filepath = os.path.join(logos_dir, filename)
        with open(filepath, "rb") as f:
            data = f.read()

        content_type = "image/png" if filename.endswith(".png") else "image/jpeg"

        try:
            supabase.storage.from_(settings.supabase_brand_images_bucket).upload(
                path=filename,
                file=data,
                file_options={"content-type": content_type, "upsert": "true"},
            )
            print(f"  Uploaded: {filename}")
        except Exception as e:
            if "Duplicate" in str(e):
                print(f"  Skipped (exists): {filename}")
            else:
                print(f"  Error uploading {filename}: {e}")

    print("Done! Brand logos uploaded to Supabase.")


if __name__ == "__main__":
    asyncio.run(seed_brand_logos())
