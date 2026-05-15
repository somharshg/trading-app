import re

def parse_strategy(text: str) -> dict:
    text_lower = text.lower()
    rules = {
        "entry": [],
        "exit": [],
        "stop_loss": None,
        "take_profit": None,
        "indicators": [],
        "timeframe": "1d"
    }

    # EMA cross detection
    ema_cross = re.search(r'(\d+)\s*ema\s*cross(?:es)?\s*above\s*(\d+)\s*ema', text_lower)
    if ema_cross:
        rules["entry"].append({
            "type": "ema_cross",
            "fast": int(ema_cross.group(1)),
            "slow": int(ema_cross.group(2)),
            "direction": "above"
        })
        rules["indicators"].extend(["EMA", f"EMA{ema_cross.group(1)}", f"EMA{ema_cross.group(2)}"])

    # RSI condition
    rsi_match = re.search(r'rsi\s*(?:is\s*)?(above|below|<|>)\s*(\d+)', text_lower)
    if rsi_match:
        rules["entry"].append({
            "type": "rsi",
            "condition": rsi_match.group(1),
            "value": int(rsi_match.group(2))
        })
        rules["indicators"].append("RSI")

    # Take profit
    tp_match = re.search(r'(\d+(?:\.\d+)?)\s*%\s*profit', text_lower)
    if tp_match:
        rules["take_profit"] = float(tp_match.group(1)) / 100

    # Stop loss
    sl_match = re.search(r'(\d+(?:\.\d+)?)\s*%\s*loss', text_lower)
    if sl_match:
        rules["stop_loss"] = float(sl_match.group(1)) / 100

    # Timeframe
    if "minute" in text_lower or "min" in text_lower:
        rules["timeframe"] = "5m"
    elif "hour" in text_lower:
        rules["timeframe"] = "1h"
    elif "week" in text_lower:
        rules["timeframe"] = "1wk"

    return rules