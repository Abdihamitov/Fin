TOPICS = {
    "budget": "💰 Бюджетирование",
    "savings": "🏦 Накопления",
    "invest": "📈 Инвестиции",
    "credit": "💳 Кредиты и долги",
    "tax": "📋 Налоги",
    "insurance": "🛡️ Страхование",
    "crypto": "₿ Криптовалюты",
    "realty": "🏠 Недвижимость",
}

TOPIC_LABELS = {v: k for k, v in TOPICS.items()}

def get_topics() -> dict:
    return TOPICS

def get_topic_name(key: str) -> str:
    return TOPICS.get(key, "Финансы")
