from dotenv import load_dotenv
import os
import json
import requests

from google import genai
from google.genai import types

load_dotenv()

API_KEY_GEMINI = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=API_KEY_GEMINI)


def download_images(image_urls: list[str]) -> list[dict]:
    """
    Descarga las imágenes y conserva la relación
    índice <-> url.
    """

    images = []

    for index, url in enumerate(image_urls):

        try:

            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                continue

            content_type = response.headers.get("Content-Type", "")

            if not content_type.startswith("image/"):
                continue

            images.append(
                {
                    "index": index,
                    "url": url,
                    "bytes": response.content,
                    "mime_type": content_type,
                }
            )

        except Exception as e:
            print(e)
            continue

    return images


def generate_prompt(
    name: str,
    ean_code: str | None = None,
    description: str | None = None,
) -> str:

    return f"""
Eres un experto clasificando imágenes de productos.

Producto

Nombre:
{name}

EAN:
{ean_code or 'No disponible'}

Descripción:
{description or "No disponible"}

Recibirás varias imágenes.

Cada imagen estará identificada con un índice:

Imagen 0
Imagen 1
Imagen 2
...

Debes evaluar cada imagen considerando:

- Marca
- Nombre
- Color del empaque
- Tipo de envase
- Presentación
- Cantidad (ml, g, kg, etc.)

Asigna un score entre 0 y 100.

100 significa coincidencia exacta.

Devuelve únicamente JSON.

Formato:

[
    {{
        "indice": 0,
        "score": 98,
        "explicacion": "Coincide exactamente."
    }}
]

No inventes campos.
No escribas texto adicional.
"""


def rank_images(
    name: str,
    image_urls: list[str],
    ean_code: str | None = None,
    description: str | None = None,
):

    downloaded_images = download_images(image_urls)

    if len(downloaded_images) == 0:
        raise Exception("No fue posible descargar ninguna imagen.")

    prompt = generate_prompt(
        name=name,
        ean_code=ean_code,
        description=description,
    )

    parts = [
        types.Part.from_text(text=prompt)
    ]

    for image in downloaded_images:

        parts.append(
            types.Part.from_text(
                text=f"Imagen {image['index']}"
            )
        )

        parts.append(
            types.Part.from_bytes(
                data=image["bytes"],
                mime_type=image["mime_type"],
            )
        )

    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=parts,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        ),
    )

    text = response.text.strip()

    print(text)

    ranking = json.loads(text)

    # Asociar la URL original utilizando el índice.
    for item in ranking:

        indice = item["indice"]

        item["image_url"] = image_urls[indice]

    ranking.sort(
        key=lambda x: x["score"],
        reverse=True,
    )

    return ranking