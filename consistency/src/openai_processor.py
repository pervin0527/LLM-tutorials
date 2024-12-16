import os
import openai
import asyncio

from typing import Dict, List, Any

from dotenv import load_dotenv
load_dotenv("/home/pervinco/LLM-tutorials/keys.env")
openai_api_key = os.getenv('GRAVY_LAB_OPENAI')

openai_client = openai.AsyncOpenAI(api_key=openai_api_key)

async def chatgpt_response(
    prompt: List[Dict[str, Any]],
    model: str = 'gpt-4o',
    retry_count: int = 1,
) -> str:

    # model = 'gpt-4o-mini'
    temperature = 0

    for attempt in range(retry_count):
        # OpenAI API 호출
        response = await openai_client.chat.completions.create(
            model=model,
            messages=prompt,
            temperature=temperature,
            seed=456
        )

        result = response.choices[0].message.content
        return result  # 성공적인 응답 반환