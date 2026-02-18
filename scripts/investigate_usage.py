import os
import json
import pandas
from openai import OpenAI
from dotenv import load_dotenv
from prompt_builder import build_prompt

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load data
operators = pandas.read_csv("../data/grid_operators.csv")
models = pandas.read_csv("../data/closed_source_ESM_frameworks.csv")

model_list = models["Name"].tolist()

results = []

for _, row in operators.iterrows():

    prompt = build_prompt(
        row["organisation"],
        row["website"],
        row["country"],
        model_list
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    content = response.choices[0].message.content

    try:
        parsed = json.loads(content)
        results.append(parsed)
    except:
        print(f"⚠ JSON parse failed for {row['organisation']}")

output = pandas.DataFrame(results)
output.to_csv("../data/esm_usage_results.csv", index=False)

print("✅ Investigation completed.")
