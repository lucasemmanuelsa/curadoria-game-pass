#!/usr/bin/env python3
"""
Xbox Game Pass — Scraper de jogos
==================================
Extrai automaticamente dados de jogos da página oficial do Xbox.
Uso:
    python scraper.py
    
Edite a lista XBOX_LINKS abaixo para adicionar/remover jogos.
"""

import os
import re
import json
import time
import hashlib
import requests
from urllib.parse import urlparse
from pathlib import Path

# ══════════════════════════════════════════════════════════════════
#   ✅ EDITE AQUI: coloque os links das páginas dos jogos no Xbox
# ══════════════════════════════════════════════════════════════════
XBOX_LINKS = [
    "https://www.xbox.com/pt-br/games/store/minecraft/9MVXMVT8ZKWC",
    "https://www.xbox.com/pt-br/games/store/planet-of-lana-ii/9pl89b9hcz9w",
    "https://www.xbox.com/pt-BR/games/store/forza-horizon-6/9NR1R1XWLCNB",
    "https://www.xbox.com/pt-BR/games/store/indiana-jones-e-o-grande-circulo/9N8FQ28Z6QX3",
    "https://www.xbox.com/pt-BR/games/store/diablo-iv/9NQRCD3W41L3",
    "https://www.xbox.com/pt-BR/games/store/resident-evil-3-for-xbox/BW3T6SNS15BH",
    "https://www.xbox.com/pt-BR/games/store/resident-evil-7-biohazard/BVFDTJ1XF6CS",
    "https://www.xbox.com/pt-BR/games/store/the-evil-within-2/C40860J5R2MP",
    "https://www.xbox.com/pt-BR/games/store/world-war-z-aftermath/9PLCL2VB2SC0",
    "https://www.xbox.com/pt-BR/games/store/star-wars-outlaws/9NLHVWSFB0FC",
    "https://www.xbox.com/pt-BR/games/store/hogwarts-legacy/9MT5NJ5W7B8Z",
    "https://www.xbox.com/pt-BR/games/store/final-fantasy-vi/9N255K81XBD3",
    "https://www.xbox.com/pt-BR/games/store/call-of-duty-black-ops-7-pacote-multigeracao/9N8KMNW6942X",
    "https://www.xbox.com/pt-BR/games/store/pax-dei/9PHGK0538TXM",
    "https://www.xbox.com/pt-BR/games/store/assassins-creed-valhalla/9P4NJFH17MRT",
    "https://www.xbox.com/pt-BR/games/store/wild-hearts/9NFT3TR6MN9W",
    "https://www.xbox.com/pt-BR/games/store/cities-skylines-ii-pc-edition/9PGZ346PSLN0",
    "https://www.xbox.com/pt-BR/games/store/age-of-empires-definitive-edition/9NJWTJSVGVLJ",
    "https://www.xbox.com/pt-BR/games/store/monsters-are-coming/9PJBKF27C16M",
    "https://www.xbox.com/pt-BR/games/store/cricket-24-the-official-game-of-the-ashes/9NKF2SZ630ZH",
    "https://www.xbox.com/pt-BR/games/store/dirt-5/9PJGM0T0827V",
    "https://www.xbox.com/pt-BR/games/store/mortal-kombat-1/9N7271QN4SGB"
]

ARQUIVO = "gamepass_links.json" 
with open(ARQUIVO, "r", encoding="utf-8") as f: 
    dados = json.load(f) 
    links = [ item["link"] for item in dados ] 

XBOX_LINKS = XBOX_LINKS + links
# ══════════════════════════════════════════════════════════════════

DATA_FILE   = Path(__file__).parent / "data" / "games.json"
IMAGES_DIR  = Path(__file__).parent / "static" / "images" / "games"

IMAGES_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    "Accept": "application/json, text/html, */*",
}

CATEGORIES_MAP = {
    "ação": "acao", "action": "acao",
    "aventura": "acao", "adventure": "acao",
    "rpg": "rpg", "role playing": "rpg",
    "shooter": "fps", "tiro": "fps", "first-person": "fps",
    "corrida": "corrida", "racing": "corrida",
    "esporte": "esporte", "sports": "esporte",
    "indie": "indie",
    "estratégia": "estrategia", "strategy": "estrategia",
}

def extract_product_id(url: str) -> str | None:
    """Extrai o bigId (Product ID) da URL do Xbox."""
    parts = url.rstrip("/").split("/")
    # Last segment that looks like a product ID (alphanumeric, ~12 chars)
    for part in reversed(parts):
        if re.match(r'^[A-Z0-9]{12}$', part.upper()) and part.isalnum():
            return part.upper()
    return None


def fetch_from_displaycatalog(product_id: str) -> dict | None:
    """Usa a API pública displaycatalog da Microsoft para buscar dados."""
    url = (
        f"https://displaycatalog.mp.microsoft.com/v7.0/products"
        f"?bigIds={product_id}&market=BR&languages=pt-br"
        f"&MS-CV=DGU1mcuYo0WMMp"
    )
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return None
        data = r.json()
        if not data.get("Products"):
            return None
        return data["Products"][0]
    except Exception as e:
        print(f"    ⚠ displaycatalog erro: {e}")
        return None


def fetch_from_xbox_page(url: str) -> dict | None:
    """
    Fallback: raspa a página do Xbox buscando dados em meta tags e JSON-LD.
    Funciona mesmo quando a API retorna 403.
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return None
        html = r.text

        result = {}

        # --- Open Graph / Meta tags ---
        og = {}
        for m in re.finditer(
            r'<meta[^>]+(?:property|name)=["\']([^"\']+)["\'][^>]+content=["\']([^"\']+)["\']',
            html
        ):
            og[m.group(1)] = m.group(2)
        for m in re.finditer(
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']([^"\']+)["\']',
            html
        ):
            og[m.group(2)] = m.group(1)

        result["title"]       = og.get("og:title", og.get("twitter:title", ""))
        result["description"] = og.get("og:description", og.get("description", ""))[:180]
        result["image_url"]   = og.get("og:image", og.get("twitter:image", ""))

        # --- JSON-LD ---
        for ld_raw in re.findall(
            r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            html, re.DOTALL
        ):
            try:
                ld = json.loads(ld_raw.strip())
                if isinstance(ld, list):
                    ld = ld[0]
                if ld.get("@type") in ("SoftwareApplication", "VideoGame", "Product"):
                    result["title"]       = result["title"] or ld.get("name", "")
                    result["description"] = result["description"] or ld.get("description", "")[:180]
                    result["developer"]   = ld.get("author", {}).get("name", "") if isinstance(ld.get("author"), dict) else ""
                    result["genre"]       = ld.get("genre", "")
                    result["rating"]      = ld.get("aggregateRating", {}).get("ratingValue", "")
                    if not result["image_url"] and ld.get("image"):
                        imgs = ld["image"]
                        result["image_url"] = imgs[0] if isinstance(imgs, list) else imgs
            except Exception:
                pass

        # --- __NEXT_DATA__ / window.__data__ ---
        for pat in [
            r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});',
            r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        ]:
            m = re.search(pat, html, re.DOTALL)
            if m:
                try:
                    nd = json.loads(m.group(1))
                    # Walk the tree looking for product info
                    flat = json.dumps(nd)
                    title_m = re.search(r'"productTitle"\s*:\s*"([^"]+)"', flat)
                    dev_m   = re.search(r'"developerName"\s*:\s*"([^"]+)"', flat)
                    desc_m  = re.search(r'"shortDescription"\s*:\s*"([^"]+)"', flat)
                    if title_m:
                        result["title"]     = title_m.group(1)
                    if dev_m:
                        result["developer"] = dev_m.group(1)
                    if desc_m:
                        result["description"] = desc_m.group(1)[:180]
                    # Images inside JSON
                    imgs = re.findall(r'"Uri"\s*:\s*"(https://[^"]+\.(?:jpg|png|jpeg)[^"]*)"', flat)
                    box_imgs = [i for i in imgs if "BoxArt" in i or "Poster" in i]
                    if box_imgs and not result.get("image_url"):
                        result["image_url"] = box_imgs[0]
                except Exception:
                    pass

        # --- Inline data patterns specific to Xbox SPA ---
        patterns = [
            (r'"productTitle"\s*:\s*"([^"]+)"', "title"),
            (r'"developerName"\s*:\s*"([^"]+)"', "developer"),
            (r'"publisherName"\s*:\s*"([^"]+)"', "publisher"),
            (r'"shortDescription"\s*:\s*"([^"]+)"', "description"),
            (r'"[Cc]ategories"\s*:\s*\["([^"]+)"', "category_raw"),
        ]
        for pattern, key in patterns:
            if not result.get(key):
                m = re.search(pattern, html)
                if m:
                    result[key] = m.group(1)

        # Find best image (BoxArt or Poster with high resolution)
        if not result.get("image_url"):
            img_candidates = re.findall(
                r'https://store-images\.s-microsoft\.com/image/apps\.[A-Za-z0-9.%_-]+',
                html
            )
            if img_candidates:
                result["image_url"] = img_candidates[0]

        return result if result.get("title") else None

    except Exception as e:
        print(f"    ⚠ xbox page scrape erro: {e}")
        return None


def parse_product_data(raw: dict, source: str) -> dict:
    """Normaliza dados da API displaycatalog para o formato do site."""
    if source == "api":
        lp   = raw.get("LocalizedProperties", [{}])[0]
        props = raw.get("MarketProperties", [{}])[0]
        pa   = raw.get("Properties", {})

        title   = lp.get("ProductTitle", "")
        dev     = lp.get("DeveloperName", lp.get("PublisherName", ""))
        desc    = (lp.get("ShortDescription") or lp.get("ProductDescription") or "")[:180]
        
        # Detect cloud gaming
        platforms  = raw.get("Platforms", [])
        cloud      = "CloudGaming" in str(platforms) or "xcloud" in str(raw).lower()

        # Categories → map to site buckets
        # API returns "Categories": null sometimes; fall back to "Category" (singular)
        cats_raw = pa.get("Categories") or []
        if not cats_raw and pa.get("Category"):
            cats_raw = [pa["Category"]]
        category = map_category(cats_raw)

        # Images
        images     = lp.get("Images", [])
        image_url  = pick_best_image(images)

        # Metacritic / rating
        rating = None
        reviews = raw.get("MarketProperties", [{}])[0].get("UsageData", [])
        for rv in reviews:
            if rv.get("AggregateTimeSpan") == "AllTime":
                rating = rv.get("AverageRating")

    else:  # scraped from page
        title     = raw.get("title", "Unknown").strip()
        # Remove "Comprar" prefix common in Xbox PT-BR page titles
        title     = re.sub(r'^Comprar\s+o?\s*', '', title, flags=re.IGNORECASE).strip()
        title     = re.sub(r'\s*\|\s*Xbox.*$', '', title).strip()
        dev       = raw.get("developer", raw.get("publisher", "")).strip()
        desc      = raw.get("description", "").strip()[:180]
        cloud     = True  # assume cloud available for Game Pass titles
        category  = map_category([raw.get("category_raw", raw.get("genre", ""))])
        image_url = raw.get("image_url", "")
        rating    = raw.get("rating")

    return dict(
        title     = title,
        developer = dev,
        description = desc,
        cloud     = cloud,
        category  = category,
        image_url = image_url,
        metacritic = int(float(rating)) if rating else None,
    )


def map_category(cats) -> str:
    cats_str = " ".join(str(c).lower() for c in (cats or []))
    for key, val in CATEGORIES_MAP.items():
        if key in cats_str:
            return val
    return "acao"


def pick_best_image(images: list) -> str:
    """Escolhe a melhor imagem BoxArt/Poster da lista de imagens da API."""
    priority = ["BoxArt", "Poster", "Logo", "SuperHeroArt", "Screenshot", "FeaturePromotionalSquareArt"]
    by_purpose = {}
    for img in images:
        purpose = img.get("ImagePurpose", "")
        uri     = img.get("Uri", "")
        if not uri:
            continue
        if not uri.startswith("http"):
            uri = "https:" + uri
        if purpose not in by_purpose:
            by_purpose[purpose] = uri

    for p in priority:
        if p in by_purpose:
            return by_purpose[p]

    # fallback
    for img in images:
        uri = img.get("Uri", "")
        if uri:
            return "https:" + uri if not uri.startswith("http") else uri
    return ""


def download_image(image_url: str, title: str) -> str | None:
    """
    Baixa a imagem e salva em static/images/games/.
    Retorna o nome do arquivo salvo ou None.
    """
    if not image_url:
        return None

    # Append high-res format hint for Xbox store images
    if "store-images.s-microsoft.com" in image_url and "?" not in image_url:
        image_url += "?w=400&h=550&q=90&format=jpg"
    elif "store-images.s-microsoft.com" in image_url and "w=" not in image_url:
        sep = "&" if "?" in image_url else "?"
        image_url += f"{sep}w=400&h=550&q=90&format=jpg"

    # Build filename from title
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:40]
    h    = hashlib.md5(image_url.encode()).hexdigest()[:6]
    ext  = ".jpg"
    filename = f"{slug}-{h}{ext}"
    filepath = IMAGES_DIR / filename

    if filepath.exists():
        print(f"    ✓ imagem já existe: {filename}")
        return filename

    try:
        r = requests.get(image_url, headers=HEADERS, timeout=20)
        if r.status_code == 200 and len(r.content) > 1000:
            filepath.write_bytes(r.content)
            print(f"    ✓ imagem baixada: {filename} ({len(r.content)//1024}KB)")
            return filename
        else:
            print(f"    ⚠ imagem não baixada (status {r.status_code}, {len(r.content)} bytes)")
            return None
    except Exception as e:
        print(f"    ⚠ erro ao baixar imagem: {e}")
        return None


def load_existing_games() -> list:
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("games", [])
    return []


def save_games(games: list):
    # Keep categories structure
    categories = [
        {"id": "destaque",    "title": "🔥 Em Destaque",         "description": "Os jogos mais jogados agora no Game Pass"},
        {"id": "acao",        "title": "⚔️ Ação & Aventura",     "description": "Adrenalina pura do início ao fim"},
        {"id": "rpg",         "title": "🧙 RPG & Mundo Aberto",  "description": "Mundos imensos para explorar"},
        {"id": "fps",         "title": "🎯 FPS & Tiro",           "description": "Precisão e estratégia nos melhores shooters"},
        {"id": "corrida",     "title": "🏎️ Corrida",             "description": "Os melhores jogos de velocidade"},
        {"id": "indie",       "title": "🎨 Indie & Exclusivos",   "description": "Experiências únicas e criativas"},
        {"id": "estrategia",  "title": "♟️ Estratégia",          "description": "Planejamento e táticas"},
        {"id": "esporte",     "title": "⚽ Esportes",             "description": "Os melhores jogos esportivos"},
    ]
    data = {"categories": categories, "games": games}
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n✅ games.json salvo com {len(games)} jogo(s).")


def process_link(url: str, existing_by_url: dict, next_id: int) -> dict | None:
    """Processa um link: busca dados e baixa imagem."""
    product_id = extract_product_id(url)
    print(f"\n🎮 Processando: {url}")
    print(f"   Product ID: {product_id}")

    # Não rebusca se já existe
    if url in existing_by_url:
        print(f"   ↩ já existe no catálogo, pulando.")
        return existing_by_url[url]

    raw    = None
    source = None

    # 1) Tenta API displaycatalog
    if product_id:
        print("   → tentando displaycatalog API...")
        raw    = fetch_from_displaycatalog(product_id)
        source = "api"

    # 2) Fallback: scrape da página
    if not raw:
        print("   → tentando scrape da página Xbox...")
        raw    = fetch_from_xbox_page(url)
        source = "page"

    if not raw:
        print("   ✗ não foi possível obter dados.")
        return None

    parsed = parse_product_data(raw, source)
    print(f"   título: {parsed['title']}")
    print(f"   dev:    {parsed['developer']}")
    print(f"   img:    {parsed['image_url'][:70] if parsed['image_url'] else '(nenhuma)'}")

    # Baixa imagem
    image_file = download_image(parsed["image_url"], parsed["title"])

    game = {
        "id":          next_id,
        "title":       parsed["title"],
        "developer":   parsed["developer"],
        "category":    parsed["category"],
        "featured":    False,
        "tags":        [],
        "description": parsed["description"],
        "image":       image_file or "placeholder.svg",
        "metacritic":  parsed.get("metacritic") or 0,
        "cloud":       parsed.get("cloud", True),
        "_source_url": url,
    }
    return game


def main():
    print("=" * 60)
    print("  Xbox Game Pass — Importador de Jogos")
    print("=" * 60)

    # Remove duplicatas mantendo ordem
    links = list(dict.fromkeys(XBOX_LINKS))
    print(f"\n{len(links)} link(s) na lista.")

    # Carrega jogos existentes
    existing = load_existing_games()
    existing_by_url = {g.get("_source_url", ""): g for g in existing if g.get("_source_url")}
    next_id = max((g.get("id", 0) for g in existing), default=0) + 1

    # Jogos vindos da lista atual de links (preserve order)
    games_out = []
    for url in links:
        game = process_link(url, existing_by_url, next_id)
        if game:
            games_out.append(game)
            if game not in existing_by_url.values():
                next_id += 1
        time.sleep(0.5)  # polite delay

    save_games(games_out)
    print("\n🚀 Reinicie o servidor Flask para ver as mudanças: python app.py")


if __name__ == "__main__":
    main()
