# 🎮 GamePass Guide — Curadoria Automática

## 📁 Estrutura do Projeto

```
gamepass-site/
├── app.py              ← Servidor Flask
├── scraper.py          ← ✅ EDITE AQUI: lista de links + importador
├── data/
│   └── games.json      ← Gerado automaticamente pelo scraper
├── static/
│   └── images/games/   ← Imagens baixadas automaticamente
└── templates/
    └── index.html
```

---

## ▶️ Como Rodar (primeira vez)

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Importar jogos (baixa dados + imagens automaticamente)
python scraper.py

# 3. Iniciar o servidor
python app.py
```

Acesse: **http://localhost:5000**

---

## ➕ Adicionar um Jogo

1. Abra `scraper.py`
2. Adicione o link do jogo na lista `XBOX_LINKS`:

```python
XBOX_LINKS = [
    "https://www.xbox.com/pt-br/games/store/minecraft/9MVXMVT8ZKWC",
    "https://www.xbox.com/pt-br/games/store/halo-infinite/9NP0H93MW1SP",
    # ← Adicione o novo link aqui
    "https://www.xbox.com/pt-br/games/store/nome-do-jogo/PRODUCTID",
]
```

3. Execute o scraper novamente:
```bash
python scraper.py
```

O scraper vai:
- Buscar automaticamente título, desenvolvedor, descrição
- Baixar a imagem oficial do Xbox
- Atualizar o `games.json`
- **Não re-baixar** jogos que já foram importados

---

## ❌ Remover um Jogo

Simplesmente remova o link correspondente de `XBOX_LINKS` em `scraper.py` e execute:

```bash
python scraper.py
```

O jogo será removido do catálogo na próxima execução.

---

## ⭐ Marcar Jogo como Destaque

Após importar, abra `data/games.json` e mude `"featured": false` para `"featured": true`
no jogo desejado. Jogos em destaque aparecem no carrossel principal do topo.

---

## 🔗 Como encontrar o link de um jogo

1. Acesse https://www.xbox.com/pt-br/xbox-game-pass/games
2. Procure o jogo desejado
3. Clique no jogo — a URL da página é o link que você precisa

Formato: `https://www.xbox.com/pt-br/games/store/NOME-DO-JOGO/PRODUCTID`

---

## 🛠️ Solução de problemas

**Imagem não aparece?**
- Verifique se o arquivo existe em `static/images/games/`
- Se não existe, tente executar `python scraper.py` novamente

**Título/descrição incorretos?**
- Edite diretamente `data/games.json` — os campos `title`, `developer`, `description` podem ser ajustados manualmente

**Categoria errada?**
- Edite `"category"` em `data/games.json`
- Valores válidos: `acao`, `rpg`, `fps`, `corrida`, `indie`, `estrategia`, `esporte`
