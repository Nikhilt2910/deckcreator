from pathlib import Path
from uuid import uuid4


def save_upload(file_name: str, file_bytes: bytes, target_dir: Path) -> dict[str, Path | str]:
    saved_name = _build_safe_name(file_name)
    saved_path = target_dir / saved_name
    saved_path.write_bytes(file_bytes)
    return {"name": saved_name, "path": saved_path}


def _build_safe_name(file_name: str) -> str:
    source = Path(file_name)
    stem = "".join(char.lower() if char.isalnum() else "-" for char in source.stem).strip("-")
    clean_stem = "-".join(part for part in stem.split("-") if part)[:50] or "file"
    suffix = source.suffix.lower()
    return f"{clean_stem}-{uuid4().hex[:8]}{suffix}"
