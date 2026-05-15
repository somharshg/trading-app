import yfinance as yf
import pandas as pd

def fetch_data(symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
        symbol = symbol + ".NS"
    
    df = yf.download(symbol, period=period, interval=interval, progress=False)
    
    if df.empty:
        raise ValueError(f"No data found for {symbol}")
    
    # Flatten MultiIndex columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # Convert UTC to IST
    if df.index.tzinfo is not None:
        df.index = df.index.tz_convert("Asia/Kolkata")
    else:
        df.index = df.index.tz_localize("Asia/Kolkata")

    df.dropna(inplace=True)
    return df

def add_indicators(df: pd.DataFrame, rules: dict) -> pd.DataFrame:
    for rule in rules.get("entry", []):
        if rule["type"] == "ema_cross":
            df[f'EMA{rule["fast"]}'] = df['Close'].ewm(span=rule["fast"]).mean()
            df[f'EMA{rule["slow"]}'] = df['Close'].ewm(span=rule["slow"]).mean()
    
    for rule in rules.get("entry", []):
        if rule["type"] == "rsi":
            delta = df['Close'].diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            avg_gain = gain.rolling(14).mean()
            avg_loss = loss.rolling(14).mean()
            rs = avg_gain / avg_loss
            df['RSI'] = 100 - (100 / (1 + rs))
    
    return df