# Vetty Assignment API

REST API that lists cryptocurrency coins and categories from CoinGecko and returns market data in Canadian dollars. When `WEBHOOK_URL` is set, a successful live market fetch sends an HTTP POST to that URL.

## Endpoints

- `GET /health` — application status and whether CoinGecko is reachable
- `GET /coins` — coin id, name, and symbol
- `GET /coin-categories` — cryptocurrency categories
- `GET /markets` — market data in CAD. Provide `coin_id` and/or `category`

List endpoints accept `page_num` (default `1`) and `per_page` (default `10`). Interactive docs are at `/docs`.

## To Run locally

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `.env`:

```
API_KEY=change-me
COINGECKO_BASE_URL=https://api.coingecko.com/api/v3
CACHE_TTL_SECONDS=60
WEBHOOK_URL=
```

Note : The WEBHOOK_URL can be obtained from webhook.site
And the API_KEY can be changed and set as needed for the env file

```powershell
fastapi dev app/main.py
```

Open http://127.0.0.1:8000/docs.

## Docker

Stop anything already using port 8000, then:

```powershell
docker build -t vetty-api .
docker run --rm -p 8000:8000 --env-file .env vetty-api
```
