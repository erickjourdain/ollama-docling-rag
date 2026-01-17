from pathlib import Path
from bs4 import BeautifulSoup

from markdown_it import MarkdownIt

from core.config import settings

def path_to_static_url(file_path: Path) -> str:
    relative_url = settings.static_url + "/" + file_path.as_posix()
    return relative_url

def md_to_html(file: Path, base_url: str) -> str:
    """Convertit le contenu Markdown en HTML simple.

    Args:
        file (str): Contenu du fichier Markdown.

    Returns:
        str: Contenu converti en HTML.
    """
    STATIC_URL = settings.static_url

    doc_filename = file.stem
    md = MarkdownIt("commonmark")

    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    html = md.render(content)

    soup = BeautifulSoup(html, 'html.parser')

    for img in soup.find_all("img"):
        src = img.get("src")
        print(f"Original img src: {src}")  # Debug line
        if not src:
            continue

        # Ignore les URLs absolues
        src = str(src)
        if src.startswith(("http://", "https://", "data:")):
            continue

        img["src"] = f"{base_url}{STATIC_URL}/temp/images/{doc_filename}/{src}"
        print(f"Updated img src: {img['src']}")  # Debug line

    return str(soup)