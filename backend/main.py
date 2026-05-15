from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from data_engine import fetch_data, add_indicators
from backtest_engine import run_backtest
import PyPDF2
import docx
import io
import os
from dotenv import load_dotenv
from groq import Groq
import json

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def parse_strategy_with_groq(strategy_text: str) -> dict:
    prompt = f"""You are a trading strategy parser. Extract the trading rules from the strategy below and return ONLY a valid JSON object with no explanation.

Strategy: {strategy_text}

Return this exact JSON structure:
{{
  "strategy_type": "indicator" or "range_breakout",
  "entry": [],
  "exit": [],
  "stop_loss": null or decimal (e.g. 0.01 for 1%),
  "take_profit": null or decimal (e.g. 0.02 for 2%),
  "target_points": null or number,
  "risk_reward": null or number (e.g. 2 for 1:2),
  "entry_after": null or "HH:MM" (24hr format),
  "timeframe": "1d" or "1h" or "15m" or "5m",
  "indicators": [],
  "levels": [] (e.g. ["CDH", "CDL", "PDH", "PDL"])
}}

For EMA cross entries add to entry array: {{"type": "ema_cross", "fast": number, "slow": number, "direction": "above" or "below"}}
For RSI entries add: {{"type": "rsi", "condition": "above" or "below", "value": number}}
For range breakout strategies set strategy_type to "range_breakout" and add relevant levels.
Return ONLY the JSON, nothing else."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)

@app.get("/")
def root():
    return {"status": "backend running"}

@app.post("/backtest")
async def backtest(
    symbol: str = Form(...),
    capital: float = Form(...),
    period: str = Form(...),
    interval: str = Form(...),
    strategy_text: str = Form(default=""),
    file: UploadFile = File(default=None)
):
    if file and file.filename:
        content = await file.read()
        if file.filename.endswith(".pdf"):
            reader = PyPDF2.PdfReader(io.BytesIO(content))
            strategy_text = " ".join(page.extract_text() for page in reader.pages)
        elif file.filename.endswith(".docx"):
            doc = docx.Document(io.BytesIO(content))
            strategy_text = " ".join(p.text for p in doc.paragraphs)

    if not strategy_text.strip():
        return {"error": "No strategy provided"}

    # Validate period vs interval compatibility
    intraday_intervals = ["1m", "2m", "5m", "15m", "30m", "60m", "1h"]
    intraday_max_periods = ["1d", "5d", "1mo"]
    if interval in intraday_intervals and period not in intraday_max_periods:
        return {"error": f"For {interval} interval, maximum period is 1 month. Please select 1 Week or 1 Month."}

    try:
        rules = parse_strategy_with_groq(strategy_text)
    except Exception as e:
        return {"error": f"Could not parse strategy: {str(e)}"}

    if not rules.get("entry") and rules.get("strategy_type") != "range_breakout":
        return {"error": "Could not identify entry conditions in your strategy"}

    try:
        df = fetch_data(symbol, period=period, interval=interval)
        df = add_indicators(df, rules)
        result = run_backtest(df, rules, capital=capital)
        result["parsed_rules"] = rules
        return result
    except Exception as e:
        return {"error": str(e)}