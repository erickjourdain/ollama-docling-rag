from pathlib import Path
import re

from core.config import settings

def path_to_static_url(file_path: Path) -> str:
    relative_url = settings.static_url + "/" + file_path.as_posix()
    return relative_url


def rewrite_markdown_image_urls(
    markdown: str,
    markdown_path: Path,
    base_url: str,
) -> str:
    """Réécrit les URLs des images dans le contenu Markdown pour pointer vers le dossier static."""

    IMAGE_MD_PATTERN = re.compile(
        r'!\[([^\]]*)\]\(([^)]+)\)'
    )
    STATIC_DIR = settings.static_dir
    STATIC_URL = settings.static_url

    def replacer(match):
        
        alt_text: str = match.group(1)
        img_path: str = match.group(2).strip()

        # Ignore URLs absolues ou déjà traitées
        if img_path.startswith(("http://", "https://", "data:", "/")):
            return match.group(0)

        # Résolution du path réel de l'image
        image_fs_path = (markdown_path.parent / img_path).resolve()

        # Sécurité : l'image doit être dans le dossier static
        if not image_fs_path.is_relative_to(STATIC_DIR.resolve()):
            return match.group(0)

        # Construction de l'URL statique
        relative_path = image_fs_path.relative_to(STATIC_DIR.resolve())
        image_url = f"{base_url}{STATIC_URL}/{relative_path.as_posix()}"
        
        return f"![{alt_text}]({image_url})"

    return IMAGE_MD_PATTERN.sub(replacer, markdown)