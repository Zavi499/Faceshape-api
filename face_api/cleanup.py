"""Image metadata management and scheduled cleanup tasks."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler

from config import CLEANUP_INTERVAL_MINUTES, IMAGE_TTL_MINUTES, META_SUFFIX, OUTPUT_DIR, ensure_output_dir

_scheduler: BackgroundScheduler | None = None


def utc_now() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""

    return datetime.now(timezone.utc)


def get_expires_at(created_at: datetime) -> datetime:
    """Return the configured expiration time for a stored image."""

    return created_at + timedelta(minutes=IMAGE_TTL_MINUTES)


def is_safe_filename(filename: str) -> bool:
    """Validate that a filename resolves to a file directly under the output directory."""

    return Path(filename).name == filename and filename not in {"", ".", ".."}


def get_image_path(filename: str) -> Path:
    """Resolve a stored image path and reject unsafe filenames."""

    if not is_safe_filename(filename):
        raise ValueError("Unsafe filename.")
    return ensure_output_dir() / filename


def get_metadata_path(filename: str) -> Path:
    """Return the sidecar metadata path for a stored image."""

    return get_image_path(filename).with_name(f"{filename}{META_SUFFIX}")


def write_image_metadata(filename: str, created_at: datetime, expires_at: datetime) -> Path:
    """Write sidecar metadata for a stored image file."""

    metadata_path = get_metadata_path(filename)
    payload = {
        "filename": filename,
        "created_at": created_at.isoformat(),
        "expires_at": expires_at.isoformat(),
    }
    metadata_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return metadata_path


def read_image_metadata(filename: str) -> dict | None:
    """Read sidecar metadata for a stored image when available."""

    metadata_path = get_metadata_path(filename)
    if not metadata_path.exists():
        return None
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def delete_image_file(filename: str) -> bool:
    """Delete a stored image and its sidecar metadata if present."""

    image_path = get_image_path(filename)
    metadata_path = get_metadata_path(filename)
    deleted = False
    if image_path.exists():
        image_path.unlink()
        deleted = True
    if metadata_path.exists():
        metadata_path.unlink()
    return deleted


def cleanup_expired_images() -> int:
    """Delete expired images and stale metadata from the output directory."""

    ensure_output_dir()
    deleted_count = 0
    now = utc_now()

    for metadata_path in OUTPUT_DIR.glob(f"*{META_SUFFIX}"):
        filename = metadata_path.name[: -len(META_SUFFIX)]
        image_path = OUTPUT_DIR / filename
        if not image_path.exists():
            metadata_path.unlink()
            continue

        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        expires_at = datetime.fromisoformat(metadata["expires_at"])
        if now >= expires_at:
            image_path.unlink(missing_ok=True)
            metadata_path.unlink(missing_ok=True)
            deleted_count += 1

    for image_path in OUTPUT_DIR.iterdir():
        if image_path.is_dir() or image_path.name.endswith(META_SUFFIX):
            continue
        metadata_path = image_path.with_name(f"{image_path.name}{META_SUFFIX}")
        if metadata_path.exists():
            continue
        file_age = now - datetime.fromtimestamp(image_path.stat().st_mtime, tz=timezone.utc)
        if file_age >= timedelta(minutes=IMAGE_TTL_MINUTES):
            image_path.unlink(missing_ok=True)
            deleted_count += 1

    return deleted_count


def start_cleanup_scheduler() -> BackgroundScheduler:
    """Start the background cleanup scheduler if it is not already running."""

    global _scheduler
    if _scheduler and _scheduler.running:
        return _scheduler

    scheduler = BackgroundScheduler(timezone=timezone.utc)
    scheduler.add_job(
        cleanup_expired_images,
        "interval",
        minutes=CLEANUP_INTERVAL_MINUTES,
        id="cleanup_expired_images",
        replace_existing=True,
    )
    scheduler.start()
    _scheduler = scheduler
    return scheduler


def stop_cleanup_scheduler() -> None:
    """Stop the background cleanup scheduler if it is running."""

    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
    _scheduler = None
