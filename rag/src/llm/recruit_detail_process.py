import os
import openai

def run_openai_api(client, prompt, input, temperature):
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": input}
        ],
        temperature=temperature
    )
    response_content = completion.choices[0].message.content
    return response_content