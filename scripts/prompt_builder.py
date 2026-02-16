def build_prompt(org_name, website, country, model_list):

    model_block = "\n".join([f"- {m}" for m in model_list])

    return f"""
You are an energy systems research analyst.

Investigate whether the following organisation uses any proprietary energy system modeling frameworks.

Organisation: {org_name}
Country: {country}
Website: {website}

Only consider the following licensed model frameworks:

{model_block}

Instructions:
- Use official website and public reports.
- Only include confirmed evidence.
- Provide reference URLs.
- Do NOT guess.
- If no evidence found, state clearly.

Return ONLY valid JSON:

{{
  "organisation": "",
  "country": "",
  "used_model_framework": "",
  "use_case": "",
  "reference_url": "",
  "confidence": "High/Medium/Low"
}}
"""
