import google.generativeai as genai
from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction="""Ты — Финн, дружелюбный и умный ИИ-ассистент по финансовой грамотности. 
Ты помогаешь людям разобраться в финансах простым и понятным языком.
Твои темы: бюджетирование, накопления, инвестиции, кредиты, страхование, налоги, личные финансы.
Отвечай на русском языке. Используй эмодзи для живости общения.
Объясняй сложные вещи простыми словами с реальными примерами.
Если тебя спрашивают не по финансовой теме — мягко направь разговор обратно к финансам.
Будь позитивным, поддерживающим и мотивирующим."""
)

async def chat_with_ai(user_id: int, message: str, history: list) -> str:
    formatted_history = []
    for role, content in history:
        gemini_role = "user" if role == "user" else "model"
        formatted_history.append({
            "role": gemini_role,
            "parts": [{"text": content}]
        })

    chat = model.start_chat(history=formatted_history)
    response = await chat.send_message_async(message)
    return response.text

async def generate_task(topic: str, level: int) -> dict:
    difficulty_map = {
        1: "очень простой, для начинающих",
        2: "лёгкий",
        3: "средний",
        4: "сложный",
        5: "экспертный"
    }
    difficulty = difficulty_map.get(level, "средний")

    prompt = f"""Создай задачу по теме "{topic}" уровня сложности: {difficulty}.

Верни ответ СТРОГО в таком формате (без лишнего текста):
ВОПРОС: [текст вопроса]
А) [вариант А]
Б) [вариант Б]
В) [вариант В]
Г) [вариант Г]
ОТВЕТ: [буква правильного ответа, только одна буква: А, Б, В или Г]
ОБЪЯСНЕНИЕ: [краткое объяснение почему этот ответ правильный]"""

    response = await model.generate_content_async(prompt)
    return parse_task(response.text, topic)

def parse_task(text: str, topic: str) -> dict:
    lines = text.strip().split('\n')
    question = ""
    options = {}
    correct = ""
    explanation = ""

    for line in lines:
        line = line.strip()
        if line.startswith("ВОПРОС:"):
            question = line.replace("ВОПРОС:", "").strip()
        elif line.startswith("А)"):
            options["А"] = line[2:].strip()
        elif line.startswith("Б)"):
            options["Б"] = line[2:].strip()
        elif line.startswith("В)"):
            options["В"] = line[2:].strip()
        elif line.startswith("Г)"):
            options["Г"] = line[2:].strip()
        elif line.startswith("ОТВЕТ:"):
            correct = line.replace("ОТВЕТ:", "").strip().upper()
        elif line.startswith("ОБЪЯСНЕНИЕ:"):
            explanation = line.replace("ОБЪЯСНЕНИЕ:", "").strip()

    return {
        "question": question,
        "options": options,
        "correct": correct,
        "explanation": explanation,
        "topic": topic
    }

async def get_financial_tip() -> str:
    prompt = "Дай один короткий (2-3 предложения) практический совет по личным финансам. Используй эмодзи. Совет должен быть конкретным и применимым сразу."
    response = await model.generate_content_async(prompt)
    return response.text
