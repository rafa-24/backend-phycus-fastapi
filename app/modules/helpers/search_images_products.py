import logging

from ddgs import DDGS

logger = logging.getLogger(__name__)


def search_images_products(query: str, max_results: int = 10) -> list[str]:
    cleaned_query = query.strip()

    if not cleaned_query:
        return []

    try:
        with DDGS() as ddgs:
            results = ddgs.images(cleaned_query, max_results=max_results)
    except Exception as exc:
        logger.exception("[DDGS Error] No se pudieron buscar imágenes: %s", exc)
        return []

    if not results:
        return []

    images_url: list[str] = []
    for item in results:
        url = item.get("image") or item.get("thumbnail")
        if url:
            images_url.append(url)

    return images_url[:max_results]
