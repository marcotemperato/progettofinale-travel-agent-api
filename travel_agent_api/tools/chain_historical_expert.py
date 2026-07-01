from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

load_dotenv()


@tool
def chain_historical_expert(input_text: str) -> str:
    """Fornisce contenuti approfonditi su un argomento storico specifico."""
    model = ChatOpenAI(model="gpt-4o")

    system_prompt = """
        You are an historical expert.
        Your mission is to provide in-depth content on the topic,
        answer questions, and act as an assistant.
        Use emojis to make your answers more engaging and friendly.
        Always strive to be approachable and helpful, offering the
        most accurate and useful information possible to users.
    """

    prompt = ChatPromptTemplate(
        [
            ("system", "{system_prompt}"),
            ("user", "{input}"),
        ]
    )

    chain = prompt | model
    result = chain.invoke(
        {
            "input": input_text,
            "system_prompt": system_prompt,
        }
    )

    print("*" * 80)
    print("chain_historical_expert")
    print("*" * 80)

    return result.content
