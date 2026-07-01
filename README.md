# Travel Agent API

Progetto finale **Specializzazione Agentic AI & Python** — assistente viaggi conversazionale con **FastAPI**, **LangChain**, **LangGraph** e **OpenAI GPT-4o**.

L'API espone un endpoint chat usato dal client web **Laravel** (`web_TravelAgent`) per pianificare viaggi: voli, hotel, itinerari e contenuti storici.

---

## Architettura

```
Browser (Laravel :8000)
        │  POST /chat/travel-agent
        ▼
FastAPI (:8080)  →  Agent (LangGraph ReAct)
                         ├── chain_historical_expert  (OpenAI)
                         ├── flights_finder           (SerpApi)
                         ├── hotels_finder            (SerpApi)
                         └── chain_travel_plan        (OpenAI)
```

---

## Requisiti

| Componente | Versione |
|------------|----------|
| Python | >= 3.10 |
| Poetry | >= 2.0 |
| Chiave OpenAI | https://platform.openai.com |
| Chiave SerpApi | https://serpapi.com |
| PHP + Composer | solo per client Laravel |
| Node.js + npm | solo per asset Laravel (opzionale) |

---

## Setup API Python

```powershell
cd travel-agent-api
poetry install
copy .env.example .env
```

Modifica `.env` con le tue chiavi:

```env
OPENAI_API_KEY="sk-..."
SERPAPI_API_KEY="..."
```

Avvia il server:

```powershell
poetry run uvicorn travel_agent_api.main:app --reload --port 8080
```

Verifica: http://127.0.0.1:8080/docs

> **Importante:** esegui sempre i comandi Poetry dalla cartella `travel-agent-api`, non da `progetto-finale`.

---

## Setup client Laravel (test end-to-end)

In un **secondo terminale**:

```powershell
cd ..\web_TravelAgent
composer install
copy .env.example .env
php artisan key:generate
php artisan serve
```

Opzionale (asset CSS/JS):

```powershell
npm install
npm run dev
```

Apri: http://localhost:8000

L'API Python deve essere già in esecuzione su porta **8080**.

---

## Struttura progetto

```
travel-agent-api/
├── travel_agent_api/
│   ├── main.py                 # FastAPI + CORS
│   ├── routes/
│   │   └── chat_router.py      # POST /chat/travel-agent
│   ├── services/
│   │   └── agent_service.py    # Agente LangGraph ReAct
│   └── tools/
│       ├── flights_finder.py
│       ├── hotels_finder.py
│       ├── chain_travel_plan.py
│       └── chain_historical_expert.py
├── tests/
├── .env.example
├── pyproject.toml
├── poetry.lock
└── README.md
```

---

## Modifiche apportate rispetto ai PDF del corso

| File | Modifica |
|------|----------|
| `flights_finder.py` / `hotels_finder.py` | Corretto bug shadowing variabile `params` → `search_params` |
| `hotels_finder.py` | Corretto typo `HoltesInputSchema` → `HotelsInputSchema` |
| `chain_travel_plan.py` | `TravelPlanInputSchema` come classe separata; import da `langchain_core` |
| `chain_historical_expert.py` | Ritorna `result.content` (stringa) invece dell'oggetto AIMessage |
| Tutti i tool + LLM | `ChatOpenAI(model="gpt-4o")` al posto di `model_name` |
| `agent_service.py` | Conversione messaggi Laravel `type: human/ai` ↔ `role: user/assistant` |
| `pyproject.toml` | Python `>=3.10,<4.0` (compatibilità `python-dotenv`) |

---

## Tracing (`print`)

Punti di log per seguire l'esecuzione nel terminale uvicorn:

| Punto | Output |
|-------|--------|
| `chat_router.py` | `chat_completion - richiesta/risposta` + messaggi |
| `agent_service.py` | `Agent.run - avvio/completato` + cronologia |
| `flights_finder` | `******** flights_finder ********` |
| `hotels_finder` | `******** hotels_finder ********` |
| `chain_travel_plan` | `******** chain_travel_plan ********` |
| `chain_historical_expert` | `******** chain_historical_expert ********` |

Quando l'agente invoca un tool, il nome compare tra le righe di asterischi.

---

## Test

### 1. Swagger (API diretta)

http://127.0.0.1:8080/docs → `POST /chat/travel-agent`

```json
{
  "messages": [
    { "role": "user", "content": "Vorrei organizzare un viaggio a Roma" }
  ]
}
```

### 2. Chat Laravel

http://localhost:8000 — scrivi nella chat e osserva il terminale API.

### 3. Prompt di esempio per tool

**Storico** (`chain_historical_expert`):
- *Raccontami la storia dell'antica Roma, concentrandoti sull'influenza sulla civiltà italiana.*

**Piano viaggio** (`chain_travel_plan`):
- *Vorrei organizzare un viaggio a Venezia dal 15 al 20 giugno 2026. Siamo una coppia, esperienza culturale, budget 2000€.*

**Voli** (`flights_finder` — richiede SerpApi):
- *Cerco voli da FCO (Roma) a CDG (Parigi) per due adulti, partenza 5 luglio 2026 e ritorno 12 luglio 2026.*

**Hotel** (`hotels_finder` — richiede SerpApi):
- *Cerco un hotel 4 stelle nel centro di Roma per due adulti dal 15 al 20 maggio 2026.*

> Le richieste con LLM/tool possono richiedere 30–120 secondi.

---

## Risoluzione problemi

| Errore | Soluzione |
|--------|-----------|
| `Poetry could not find pyproject.toml` | Entra in `travel-agent-api` prima dei comandi |
| `WinError 10013` porta 8080 | Chiudi processo precedente: `netstat -ano \| findstr ":8080"` poi `taskkill /PID <pid> /F` |
| Chat Laravel senza risposta AI | Verifica API su :8080 e chiavi in `.env` |
| `RequestsDependencyWarning` | Warning innocuo, ignorabile |

---

## Documentazione corso

I PDF guida (01–06) sono nella root di questa cartella.

---

## Autore

Marco — Progetto finale Aulab Hackademy 2025
