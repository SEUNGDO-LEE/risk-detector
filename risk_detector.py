# risk_detector.py
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def detect_risk(text: str) -> str:
    prompt = (
        "다음 콘텐츠에서 사회적, 정치적, 윤리적 또는 법적 리스크 요소를 요약해줘. "
        "리스크가 있는 경우 해당 문장을 직접 인용해서 표시해줘.\n\n"
        f"{text}"
    )
    
    
    chat_completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return chat_completion.choices[0].message.content

