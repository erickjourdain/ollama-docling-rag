from pathlib import Path


def delete_file(file_path: Path) -> bool:
    try:
        # Suppression du fichier temporaire
        file_path.unlink()
        return True
    except Exception as e:
        raise ValueError(e)