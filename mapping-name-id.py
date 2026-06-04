import json
import requests
from urllib.parse import quote

INPUT_FILE = "jogos.txt"

OUTPUT_FOUND = "gamepass_links.json"
OUTPUT_NOT_FOUND = "nao_encontrados.json"

SEARCH_URL = (
    "https://displaycatalog.mp.microsoft.com/"
    "v7.0/productFamilies/autosuggest"
)

PRODUCTS_URL = (
    "https://displaycatalog.mp.microsoft.com/"
    "v7.0/products"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def buscar_primeiro_product_id(nome_jogo):
    params = {
        "languages": "pt-br",
        "market": "BR",
        "platformdependencyname": "windows.xbox",
        "topProducts": 10,
        "query": nome_jogo,
        "productFamilyNames": "Games"
    }

    try:
        response = requests.get(
            SEARCH_URL,
            params=params,
            headers=HEADERS,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        results = data.get("Results", [])

        if not results:
            return None

        for grupo in results:
            produtos = grupo.get("Products", [])

            if produtos:
                return produtos[0]["ProductId"]

        return None

    except Exception as e:
        print(f"Erro ao buscar ProductId de '{nome_jogo}': {e}")
        return None


def jogo_esta_no_gamepass(product_id):
    params = {
        "bigIds": product_id,
        "market": "BR",
        "languages": "pt-br"
    }

    try:
        response = requests.get(
            PRODUCTS_URL,
            params=params,
            headers=HEADERS,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        produtos = data.get("Products", [])

        if not produtos:
            return False

        produto = produtos[0]

        texto_json = json.dumps(produto).lower()

        keywords = [
            "gamepass",
            "game pass",
            "xboxgamepass",
            "includedinsubscription",
            "gamepassultimate"
        ]

        return any(
            keyword in texto_json
            for keyword in keywords
        )

    except Exception as e:
        print(f"Erro ao verificar Game Pass '{product_id}': {e}")
        return False


def montar_link(nome_jogo, product_id):
    slug = nome_jogo.lower()

    slug = (
        slug.replace(":", "")
        .replace("'", "")
        .replace('"', "")
        .replace(".", "")
        .replace(",", "")
        .replace("  ", " ")
        .replace(" ", "-")
    )

    slug = quote(slug)

    return (
        f"https://www.xbox.com/pt-BR/games/store/"
        f"{slug}/{product_id}"
    )


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        jogos = [
            linha.strip()
            for linha in f
            if linha.strip()
        ]

    encontrados = []
    nao_encontrados = []

    for jogo in jogos:
        print(f"\nBuscando: {jogo}")

        product_id = buscar_primeiro_product_id(jogo)

        if not product_id:
            print("Não encontrado.")
            nao_encontrados.append({
                "game": jogo,
                "reason": "ProductId não encontrado"
            })
            continue

        print(f"ProductId: {product_id}")

        if not jogo_esta_no_gamepass(product_id):
            print("Não está no Game Pass.")

            nao_encontrados.append({
                "game": jogo,
                "product_id": product_id,
                "reason": "Não está no Game Pass"
            })

            continue

        link = montar_link(jogo, product_id)

        print("Game Pass OK!")
        print(link)

        encontrados.append({
            "game": jogo,
            "product_id": product_id,
            "link": link
        })

    with open(OUTPUT_FOUND, "w", encoding="utf-8") as f:
        json.dump(
            encontrados,
            f,
            ensure_ascii=False,
            indent=4
        )

    with open(OUTPUT_NOT_FOUND, "w", encoding="utf-8") as f:
        json.dump(
            nao_encontrados,
            f,
            ensure_ascii=False,
            indent=4
        )

    print(f"\nSalvo encontrados em: {OUTPUT_FOUND}")
    print(f"Salvo não encontrados em: {OUTPUT_NOT_FOUND}")


if __name__ == "__main__":
    main()

