import pandas as pd

def run_backtest(df: pd.DataFrame, rules: dict, capital: float = 100000, fee_pct: float = 0.001) -> dict:
    strategy_type = rules.get("strategy_type", "indicator")
    if strategy_type == "range_breakout":
        return run_range_breakout(df, rules, capital, fee_pct)
    else:
        return run_indicator_backtest(df, rules, capital, fee_pct)


def run_range_breakout(df: pd.DataFrame, rules: dict, capital: float, fee_pct: float) -> dict:
    trades = []
    equity = [capital]
    current_capital = capital
    target_points = rules.get("target_points")
    risk_reward = rules.get("risk_reward", 2)
    entry_after = rules.get("entry_after", "10:15")
    hour, minute = map(int, entry_after.split(":"))

    df.index = pd.to_datetime(df.index)
    dates = df.index.normalize().unique()

    for i in range(1, len(dates)):
        today = dates[i]
        yesterday = dates[i - 1]

        today_data = df[df.index.normalize() == today]
        yesterday_data = df[df.index.normalize() == yesterday]

        if today_data.empty or yesterday_data.empty:
            continue

        pre_range = today_data[
            (today_data.index.hour < hour) |
            ((today_data.index.hour == hour) & (today_data.index.minute < minute))
        ]
        if pre_range.empty:
            continue

        cdh = float(pre_range['High'].max())
        cdl = float(pre_range['Low'].min())
        pdh = float(yesterday_data['High'].max())
        pdl = float(yesterday_data['Low'].min())

        long_level = max(cdh, pdh)
        short_level = min(cdl, pdl)

        filtered = today_data[
            (today_data.index.hour > hour) |
            ((today_data.index.hour == hour) & (today_data.index.minute >= minute))
        ]

        trade_taken = False
        for idx, row in filtered.iterrows():
            if trade_taken:
                break

            close = float(row['Close'])
            date_str = idx.strftime("%Y-%m-%d")
            time_str = idx.strftime("%H:%M")

            if close > long_level:
                direction = "long"
                entry_price = close
            elif close < short_level:
                direction = "short"
                entry_price = close
            else:
                continue

            shares = int(current_capital / entry_price)
            if shares == 0:
                continue

            if target_points:
                if direction == "long":
                    tp_price = entry_price + target_points
                    sl_price = entry_price - (target_points / risk_reward)
                else:
                    tp_price = entry_price - target_points
                    sl_price = entry_price + (target_points / risk_reward)
            else:
                if direction == "long":
                    tp_price = entry_price * 1.02
                    sl_price = entry_price * 0.99
                else:
                    tp_price = entry_price * 0.98
                    sl_price = entry_price * 1.01

            exit_price = None
            exit_reason = None
            exit_date = date_str

            remaining = filtered[filtered.index > idx]
            for eidx, erow in remaining.iterrows():
                h = float(erow['High'])
                l = float(erow['Low'])

                if direction == "long":
                    if l <= sl_price:
                        exit_price = sl_price
                        exit_reason = "stop_loss"
                        exit_date = eidx.strftime("%Y-%m-%d %H:%M")
                        break
                    if h >= tp_price:
                        exit_price = tp_price
                        exit_reason = "take_profit"
                        exit_date = eidx.strftime("%Y-%m-%d %H:%M")
                        break
                else:
                    if h >= sl_price:
                        exit_price = sl_price
                        exit_reason = "stop_loss"
                        exit_date = eidx.strftime("%Y-%m-%d %H:%M")
                        break
                    if l <= tp_price:
                        exit_price = tp_price
                        exit_reason = "take_profit"
                        exit_date = eidx.strftime("%Y-%m-%d %H:%M")
                        break

            if exit_price is None:
                exit_price = float(filtered.iloc[-1]['Close'])
                exit_reason = "end_of_day"
                exit_date = date_str

            if direction == "long":
                pnl = (exit_price - entry_price) * shares
            else:
                pnl = (entry_price - exit_price) * shares

            pnl -= (entry_price * shares * fee_pct) + (exit_price * shares * fee_pct)
            current_capital += pnl
            current_capital = max(current_capital, 0)

            trades.append({
                "entry_date": f"{date_str} {time_str}",
                "exit_date": exit_date,
                "entry_price": round(entry_price, 2),
                "exit_price": round(exit_price, 2),
                "shares": shares,
                "direction": direction,
                "pnl": round(pnl, 2),
                "pnl_pct": round((pnl / (entry_price * shares)) * 100, 2),
                "exit_reason": exit_reason
            })

            equity.append(current_capital)
            trade_taken = True

    return compute_analytics(trades, equity, capital)


def run_indicator_backtest(df: pd.DataFrame, rules: dict, capital: float, fee_pct: float) -> dict:
    trades = []
    position = None
    equity = [capital]
    current_capital = capital

    for i in range(1, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i - 1]
        close = float(row['Close'])
        date = str(df.index[i].date())

        if position is None:
            entry_signal = check_entry(row, prev, rules)
            if entry_signal:
                shares = int(current_capital / close)
                if shares > 0:
                    position = {
                        "entry_price": close,
                        "shares": shares,
                        "entry_date": date,
                        "cost": shares * close * (1 + fee_pct)
                    }
                    current_capital -= position["cost"]

        elif position is not None:
            exit_reason = check_exit(close, position, rules)
            if exit_reason:
                proceeds = position["shares"] * close * (1 - fee_pct)
                pnl = proceeds - position["cost"]
                current_capital += proceeds
                trades.append({
                    "entry_date": position["entry_date"],
                    "exit_date": date,
                    "entry_price": position["entry_price"],
                    "exit_price": close,
                    "shares": position["shares"],
                    "pnl": round(pnl, 2),
                    "pnl_pct": round((pnl / position["cost"]) * 100, 2),
                    "exit_reason": exit_reason
                })
                position = None

        equity.append(current_capital + (position["shares"] * close if position else 0))

    return compute_analytics(trades, equity, capital)


def check_entry(row, prev, rules) -> bool:
    signals = []
    for rule in rules.get("entry", []):
        if rule["type"] == "ema_cross":
            fast = f'EMA{rule["fast"]}'
            slow = f'EMA{rule["slow"]}'
            if fast in row and slow in row:
                crossed = float(prev[fast]) <= float(prev[slow]) and float(row[fast]) > float(row[slow])
                signals.append(crossed)
        elif rule["type"] == "rsi":
            if 'RSI' in row:
                val = float(row['RSI'])
                if rule["condition"] in ["below", "<"]:
                    signals.append(val < rule["value"])
                else:
                    signals.append(val > rule["value"])
    return all(signals) if signals else False


def check_exit(close: float, position: dict, rules: dict) -> str:
    entry = position["entry_price"]
    change = (close - entry) / entry
    if rules.get("take_profit") and change >= rules["take_profit"]:
        return "take_profit"
    if rules.get("stop_loss") and change <= -rules["stop_loss"]:
        return "stop_loss"
    return None


def compute_analytics(trades: list, equity: list, initial_capital: float) -> dict:
    if not trades:
        return {"error": "No trades executed with this strategy"}

    total = len(trades)
    wins = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] <= 0]
    net_pnl = sum(t["pnl"] for t in trades)
    win_rate = round(len(wins) / total * 100, 2)

    avg_win = round(sum(t["pnl"] for t in wins) / len(wins), 2) if wins else 0
    avg_loss = round(sum(t["pnl"] for t in losses) / len(losses), 2) if losses else 0

    peak = equity[0]
    max_dd = 0
    for e in equity:
        if e > peak:
            peak = e
        dd = (peak - e) / peak
        if dd > max_dd:
            max_dd = dd

    returns = [t["pnl_pct"] for t in trades]
    avg_return = sum(returns) / len(returns)
    std_return = pd.Series(returns).std()
    sharpe = round(avg_return / std_return, 2) if std_return > 0 else 0

    return {
        "total_trades": total,
        "winning_trades": len(wins),
        "losing_trades": len(losses),
        "win_rate": win_rate,
        "net_pnl": round(net_pnl, 2),
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "max_drawdown": round(max_dd * 100, 2),
        "sharpe_ratio": sharpe,
        "profit_expectancy": round((win_rate/100 * avg_win) + ((1 - win_rate/100) * avg_loss), 2),
        "equity_curve": equity,
        "trades": trades
    }