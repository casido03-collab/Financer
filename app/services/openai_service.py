from openai import AsyncOpenAI
from app.config import OPENAI_API_KEY
from app.texts.prompts import (
    SYSTEM_PROMPT,
    PLAN_5_DAYS_PROMPT,
    PLAN_14_DAYS_PROMPT,
    EXPENSE_ANALYSIS_PROMPT,
    DEBT_PLAN_PROMPT,
)

client = AsyncOpenAI(api_key=OPENAI_API_KEY)


async def get_ai_response(user_message: str, system: str = SYSTEM_PROMPT) -> str:
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_message},
            ],
            max_tokens=1500,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Произошла ошибка при обращении к ИИ. Попробуйте позже. ({type(e).__name__})"


async def generate_5_day_plan(user_data: dict) -> str:
    user_data_str = "\n".join(f"{k}: {v}" for k, v in user_data.items())
    prompt = PLAN_5_DAYS_PROMPT.format(user_data=user_data_str)
    return await get_ai_response(prompt)


async def generate_14_day_plan(user_data: dict) -> str:
    user_data_str = "\n".join(f"{k}: {v}" for k, v in user_data.items())
    prompt = PLAN_14_DAYS_PROMPT.format(user_data=user_data_str)
    return await get_ai_response(prompt)


async def analyze_expenses(expense_data: str, user_profile: dict) -> str:
    profile_str = "\n".join(f"{k}: {v}" for k, v in user_profile.items() if v)
    prompt = EXPENSE_ANALYSIS_PROMPT.format(
        expense_data=expense_data,
        user_profile=profile_str,
    )
    return await get_ai_response(prompt)


async def generate_debt_plan(debt_data: str, user_profile: dict) -> str:
    profile_str = "\n".join(f"{k}: {v}" for k, v in user_profile.items() if v)
    prompt = DEBT_PLAN_PROMPT.format(
        debt_data=debt_data,
        user_profile=profile_str,
    )
    return await get_ai_response(prompt)
