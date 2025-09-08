from openai import OpenAI

client = OpenAI(
    api_key="8d7f559e971d49579d719f5bf40589d8.eJxWWgsNZUe9Pcc9",
    base_url="https://api.z.ai/api/paas/v4/"
)

completion = client.chat.completions.create(
    model="glm-4.5",
    messages=[
        {"role": "system", "content": "You are a smart and creative novelist"},
        {"role": "user", "content": "Please write a short fairy tale story as a fairy tale master"}
    ]
)

print(completion.choices[0].message.content)