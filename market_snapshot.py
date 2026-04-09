import os
import requests
from dotenv import load_dotenv


BINANCE_TICKER_URL = "https://api.binance.com/api/v3/ticker/24hr"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def get_range_position(last_price: float, low_price: float, high_price: float) -> float:
    if high_price == low_price:
        return 50.0
    return ((last_price - low_price) / (high_price - low_price)) * 100


def get_market_data(symbol: str) -> dict:
    response = requests.get(BINANCE_TICKER_URL, params={"symbol": symbol}, timeout=30)
    response.raise_for_status()
    data = response.json()

    last_price = float(data["lastPrice"])
    high_price = float(data["highPrice"])
    low_price = float(data["lowPrice"])

    return {
        "symbol": data["symbol"],
        "last_price": last_price,
        "price_change_percent": float(data["priceChangePercent"]),
        "high_price": high_price,
        "low_price": low_price,
        "volume": float(data["volume"]),
        "quote_volume": float(data["quoteVolume"]),
        "range_position_percent": get_range_position(last_price, low_price, high_price),
    }


def format_market_block(data: dict) -> str:
    return (
        f"{data['symbol']}\n"
        f"Last Price: {data['last_price']:.2f}\n"
        f"24h Change: {data['price_change_percent']:.2f}%\n"
        f"24h High: {data['high_price']:.2f}\n"
        f"24h Low: {data['low_price']:.2f}\n"
        f"24h Volume: {data['volume']:.2f}\n"
        f"24h Quote Volume: {data['quote_volume']:.2f}\n"
        f"Range Position: {data['range_position_percent']:.2f}%\n"
    )


def build_prompt(market_data_list: list[dict]) -> str:
    blocks = "\n".join(format_market_block(item) for item in market_data_list)

    return (
        "You are a crypto market analyst. "
        "Review the following 24 hour spot market data and write a concise market snapshot. "
        "Focus on relative strength, weakness, and what the range position implies. "
        "Do not give generic disclaimers. "
        "Keep the answer to about 6 to 10 sentences.\n\n"
        f"{blocks}"
    )


def get_ai_summary(prompt: str, api_key: str) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
    }

    response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()

    return data["choices"][0]["message"]["content"]


def main() -> None:
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise ValueError("Missing OPENROUTER_API_KEY in .env file")

    symbols = ["BTCUSDT", "ETHUSDT"]
    market_data = [get_market_data(symbol) for symbol in symbols]

    print("Market Data\n")
    for item in market_data:
        print(format_market_block(item))

    prompt = build_prompt(market_data)
    ai_summary = get_ai_summary(prompt, api_key)

    print("\nAI Market Summary\n")
    print(ai_summary)


if __name__ == "__main__":
    main()