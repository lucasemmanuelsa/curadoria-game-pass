import requests

query = "avowed"

url = (
    "https://displaycatalog.mp.microsoft.com/"
    "v7.0/productFamilies/autosuggest"
)

params = {
    "languages": "pt-br",
    "market": "BR",
    "platformdependencyname": "windows.xbox",
    "topProducts": 25,
    "query": query,
    "productFamilyNames": "Games"
}

data = requests.get(url, params=params).json()

print(data)