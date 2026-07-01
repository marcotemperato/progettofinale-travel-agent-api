from datetime import datetime

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from travel_agent_api.tools.chain_historical_expert import chain_historical_expert
from travel_agent_api.tools.chain_travel_plan import chain_travel_plan
from travel_agent_api.tools.flights_finder import flights_finder
from travel_agent_api.tools.hotels_finder import hotels_finder

load_dotenv()

FLIGHTS_OUTPUT = """format: markdown
    ## Miglior Opzione
    ### Andata:
    - Compagnia aerea: Ryanair
    - Data di partenza: 2024-12-13
    - Ora di partenza: 10:00
    - Durata del volo: 1h 30m
    ### Ritorno:
    - Compagnia aerea: Ryanair
    - Data di ritorno: 2024-12-19
    - Ora di ritorno: 14:30
    - Durata del volo: 1h 30m
    Inserisci il link di Google per la prenotazione se possibile.
    #### Altri opzioni disponibili:
    - Compagnia aerea: Ryanair
    - Data di partenza: 2024-12-13
    - Ora di partenza: 10:00
    - Durata del volo: 1h 30m
    - Compagnia aerea: Ryanair
    - Data di ritorno: 2024-12-19
    - Ora di ritorno: 14:30
    - Durata del volo: 1h 30m
    ..."""

HOTELS_OUTPUT = """format: markdown
    #### Hotel 1
    Inserisci la foto dell'hotel se disponibile.
    *Descrizione:* Camere e suite eleganti, a volte con vista sulla citta', in hotel esclusivo con piscina panoramica e spa.
    *Prezzo per notte:* EUR296 (prima delle tasse e spese: EUR260)
    *Prezzo totale:* EUR2,660 (prima delle tasse e spese: EUR2,336)
    *Check-in:* 15:00, Check-out: 12:00
    *Valutazione complessiva:* 4.5 su 5
    *Servizi Inclusi:* Spa, Piscina, Parcheggio gratuito
    #### Hotel 2
    Inserisci la foto dell'hotel se disponibile.
    Descrizione: Hotel in stile Liberty con alloggi arredati in maniera artistica, ristorante elegante, bar e spa.
    *Prezzo per notte:* EUR380 (prima delle tasse e spese: EUR333)
    *Prezzo totale:* EUR3,418 (prima delle tasse e spese: EUR3,000)
    *Check-in:* 15:00, Check-out: 12:00
    *Valutazione complessiva:* 4.5 su 5
    *Servizi Inclusi:* Spa, Piscina, Parcheggio gratuito
"""

TRAVEL_PLAN_OUTPUT = """format: markdown
    ### Itinerario:
    ### Giorno 1 - 2024-12-13:
    *Mattina:* Descrizione dell'attivita' da svolgere la mattina
    *Pomeriggio:* Descrizione dell'attivita' da svolgere il pomeriggio
    *Sera:* Descrizione dell'attivita' da svolgere la sera
    ### Giorno 2 - 2024-12-14:
    *Mattina:* Descrizione dell'attivita' da svolgere la mattina
    *Pomeriggio:* Descrizione dell'attivita' da svolgere il pomeriggio
    *Sera:* Descrizione dell'attivita' da svolgere la sera
    ..."""


def _extract_content(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and "text" in part:
                parts.append(str(part["text"]))
            else:
                parts.append(str(part))
        return " ".join(parts)
    return str(content)


def _to_agent_messages(messages: list) -> list:
    """Converte messaggi Laravel (type human/ai) in formato role user/assistant."""
    agent_messages = []

    for message in messages:
        role = message.get("role")
        msg_type = message.get("type")
        content = _extract_content(message.get("content", ""))

        if msg_type == "human" or role in ("user", "human"):
            agent_messages.append({"role": "user", "content": content})
        elif msg_type == "ai" or role in ("assistant", "ai"):
            agent_messages.append({"role": "assistant", "content": content})
        elif role in ("user", "assistant"):
            agent_messages.append({"role": role, "content": content})

    return agent_messages


def _message_to_laravel(message) -> dict | None:
    if isinstance(message, HumanMessage):
        return {"type": "human", "content": _extract_content(message.content)}

    if isinstance(message, AIMessage):
        content = _extract_content(message.content)
        if not content:
            return None
        return {"type": "ai", "content": content}

    if isinstance(message, BaseMessage):
        message_type = getattr(message, "type", "")
        content = _extract_content(message.content)
        if message_type == "human":
            return {"type": "human", "content": content}
        if message_type == "ai" and content:
            return {"type": "ai", "content": content}
        return None

    if isinstance(message, dict):
        role = message.get("role")
        msg_type = message.get("type")
        content = _extract_content(message.get("content", ""))

        if msg_type == "human" or role in ("user", "human"):
            return {"type": "human", "content": content}
        if msg_type == "ai" or role in ("assistant", "ai"):
            return {"type": "ai", "content": content} if content else None

    return None


def _to_laravel_messages(messages: list) -> list:
    laravel_messages = []

    for message in messages:
        converted = _message_to_laravel(message)
        if converted:
            laravel_messages.append(converted)

    return laravel_messages


class Agent:
    def __init__(self):
        self.current_datetime = datetime.now()
        self.model = ChatOpenAI(model="gpt-4o")
        self.tools = [
            chain_historical_expert,
            flights_finder,
            hotels_finder,
            chain_travel_plan,
        ]
        self.agent_executor = create_react_agent(self.model, self.tools)

    def run(self, messages: list):
        print("*" * 80)
        print("Agent.run - avvio")
        print("messaggi ricevuti:", messages)
        print("*" * 80)

        system_prompt = f"""
            Sei un travel planner. Il tuo compito e' organizzare il viaggio per l'utente.
            Aggiungi delle emojis per rendere il tuo output piu' interessante.
            La data di oggi e' {self.current_datetime}

            Usa le seguenti istruzioni per creare un output:

            Esempio Ouput Voli:
            {FLIGHTS_OUTPUT}

            Esempio Output Hotel:
            {HOTELS_OUTPUT}

            Esempio di Output Viaggio:
            {TRAVEL_PLAN_OUTPUT}
        """

        agent_messages = _to_agent_messages(messages)
        conversation_history = [{"role": "system", "content": system_prompt}] + agent_messages

        print("[TRACE] conversation_history inviata all'agente:", conversation_history)

        response = self.agent_executor.invoke({"messages": conversation_history})
        agent_response_messages = response["messages"][1:]

        print("[TRACE] messaggi risposta agente:", agent_response_messages)

        laravel_messages = _to_laravel_messages(agent_response_messages)

        print("*" * 80)
        print("Agent.run - completato")
        print("messaggi per Laravel:", laravel_messages)
        print("*" * 80)

        return laravel_messages
