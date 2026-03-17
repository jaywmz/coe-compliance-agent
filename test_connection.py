from openai import AzureOpenAI

client = AzureOpenAI(
    api_key="CzwZKLnpuaYmmuPgB4lV3BDHLj0dmVL0ZeTBzp9ixSlWiJ7mEwQ7JQQJ99CCACfhMk5XJ3w3AAAAACOGUhjs",
    api_version="2024-12-01-preview",
    azure_endpoint="https://23010-mmu8baa4-swedencentral.cognitiveservices.azure.com/"
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are an Azure DevOps CI/CD governance expert."},
        {"role": "user", "content": "What is a YAML template hierarchy in Azure DevOps?"}
    ],
    max_tokens=200
)

print("--- Connection successful! ---")
print(response.choices[0].message.content)