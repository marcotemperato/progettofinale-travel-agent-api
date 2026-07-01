from typing import Optional

from dotenv import load_dotenv
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

load_dotenv()


class TravelPlanInput(BaseModel):
    start_date: str = Field(description="The start date of the trip (YYYY-MM-DD) e.g. 2024-12-13.")
    end_date: str = Field(description="The end date of the trip (YYYY-MM-DD) e.g. 2024-12-19.")
    destination: str = Field(description="The destination of the trip.")
    adults: Optional[int] = Field(1, description="The number of adults. Defaults to 1.")
    children: Optional[int] = Field(0, description="The number of children. Defaults to 0.")
    travel_style: str = Field(
        description="The style of travel. e.g. adventure, relax, culture, backpacking, luxury, family-friendly."
    )
    budget: Optional[int] = Field(default=None, description="The total budget for the trip.")
    activities: str = Field(
        default="culture, food, sightseeing",
        description="The preferred activities. e.g. culture, nature, food, shopping.",
    )
    food_restriction: str = Field(
        default="none",
        description="Any food restrictions. e.g. vegetarian, gluten-free.",
    )


class TravelPlanInputSchema(BaseModel):
    params: TravelPlanInput


class TravelDayOutput(BaseModel):
    morning: str = Field(description="The activities for the morning.")
    afternoon: str = Field(description="The activities for the afternoon.")
    evening: str = Field(description="The activities for the evening.")


class TravelPlanOutput(BaseModel):
    travel_plan: list[TravelDayOutput]


@tool(args_schema=TravelPlanInputSchema)
def chain_travel_plan(params: TravelPlanInput):
    """Generates a comprehensive travel plan based on user input parameters."""
    try:
        model = ChatOpenAI(model="gpt-4o")
        output_parser = PydanticOutputParser(pydantic_object=TravelPlanOutput)
        format_instructions = output_parser.get_format_instructions()

        system_prompt = f"""
        You are a travel expert.
        Your mission is to provide in-depth content on the topic to create a travel plan.
        The start date of the trip is {params.start_date}.
        The end date of the trip is {params.end_date}.
        The destination of the trip is {params.destination}.
        The number of adults is {params.adults}.
        The number of children is {params.children}.
        The style of travel is {params.travel_style}.
        The total budget for the trip is {params.budget}.
        The preferred activities are {params.activities}.
        Any food restrictions are {params.food_restriction}
        Use emojis to make your answers more engaging and friendly.
        Always strive to be approachable and helpful, offering the
        most accurate and useful information possible to users.

        {format_instructions}
        """

        prompt = ChatPromptTemplate([("human", "{input}")])
        chain = prompt | model | output_parser
        result = chain.invoke({"input": system_prompt})

        print("*" * 80)
        print("chain_travel_plan")
        print("*" * 80)

        return result.model_dump()
    except Exception as e:
        print("Error chain_travel_plan:", e)
        return f"Errore nella generazione del piano viaggio: {e}"
