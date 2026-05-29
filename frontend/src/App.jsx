import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts"
import { useState, useEffect } from "react"
import { supabase } from "./supabase"

export default function App() {
  const [user, setUser] = useState(null)
  const [usageCount, setUsageCount] = useState(0)
  const [symbol, setSymbol] = useState("")
  const [capital, setCapital] = useState("")
  const [period, setPeriod] = useState("1y")
  const [interval, setInterval] = useState("1d")
  const [strategyText, setStrategyText] = useState("")
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null)
      if (session?.user) fetchUsage(session.user.id)
    })
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null)
      if (session?.user) fetchUsage(session.user.id)
    })
    return () => subscription.unsubscribe()
  }, [])

  const fetchUsage = async (userId) => {
    const today = new Date().toISOString().split("T")[0]
    const { data } = await supabase
      .from("usage")
      .select("count")
      .eq("user_id", userId)
      .eq("date", today)
      .single()
    setUsageCount(data?.count ?? 0)
  }

  const incrementUsage = async (userId) => {
    const today = new Date().toISOString().split("T")[0]
    const { data } = await supabase
      .from("usage")
      .select("count")
      .eq("user_id", userId)
      .eq("date", today)
      .single()

    if (data) {
      await supabase.from("usage").update({ count: data.count + 1 }).eq("user_id", userId).eq("date", today)
      setUsageCount(data.count + 1)
    } else {
      await supabase.from("usage").insert({ user_id: userId, date: today, count: 1 })
      setUsageCount(1)
    }
  }

  const loginWithGoogle = async () => {
    await supabase.auth.signInWithOAuth({ provider: "google" })
  }

  const logout = async () => {
    await supabase.auth.signOut()
    setUser(null)
    setResult(null)
  }

  const runBacktest = async () => {
    if (usageCount >= 5) {
      setError("You have used all 5 backtests for today. Come back tomorrow.")
      return
    }

    setLoading(true)
    setError("")
    setResult(null)

    const formData = new FormData()
    formData.append("symbol", symbol)
    formData.append("capital", capital)
    formData.append("period", period)
    formData.append("interval", interval)
    formData.append("strategy_text", strategyText)
    if (file) formData.append("file", file)

    try {
      const res = await fetch("https://trading-app-3cv8.onrender.com/backtest", {
        method: "POST",
        body: formData
      })
      const data = await res.json()
      if (data.error) {
        setError(data.error)
      } else {
        setResult(data)
        await incrementUsage(user.id)
      }
    } catch (e) {
      setError("Backend not reachable. Make sure it is running.")
    }

    setLoading(false)
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-950 text-white flex flex-col items-center justify-center gap-6">
        <h1 className="text-3xl font-bold text-green-400">Strategy Backtester</h1>
        <p className="text-gray-400 text-center max-w-md">Backtest any trading strategy in plain English. Login to get started.</p>
        <button
          className="bg-white text-black font-bold px-6 py-3 rounded flex items-center gap-3 hover:bg-gray-100"
          onClick={loginWithGoogle}
        >
          <img src="https://www.google.com/favicon.ico" className="w-5 h-5" />
          Sign in with Google
        </button>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      <div className="flex justify-between items-center mb-8 max-w-4xl">
        <h1 className="text-3xl font-bold text-green-400">Strategy Backtester</h1>
        <div className="flex items-center gap-4">
          <span className="text-gray-400 text-sm">{5 - usageCount} backtests left today</span>
          <span className="text-gray-400 text-sm">{user.email}</span>
          <button onClick={logout} className="text-sm text-red-400 hover:text-red-300">Logout</button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl">
        <div className="flex flex-col gap-4">
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Stock Symbol (NSE)</label>
            <input
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white"
              placeholder="e.g. RELIANCE, BANKNIFTY, NIFTY"
              value={symbol}
              onChange={e => setSymbol(e.target.value)}
            />
          </div>
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Capital (₹)</label>
            <input
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white"
              placeholder="e.g. 100000"
              type="number"
              value={capital}
              onChange={e => setCapital(e.target.value)}
            />
          </div>
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Backtest Period</label>
            <select className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white" value={period} onChange={e => setPeriod(e.target.value)}>
              <option value="5d">1 Week</option>
              <option value="1mo">1 Month</option>
              <option value="3mo">3 Months</option>
              <option value="6mo">6 Months</option>
              <option value="1y">1 Year</option>
              <option value="2y">2 Years</option>
              <option value="5y">5 Years</option>
            </select>
          </div>
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Candle Interval</label>
            <select className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white" value={interval} onChange={e => setInterval(e.target.value)}>
              <option value="1d">Daily</option>
              <option value="1wk">Weekly</option>
              <option value="1h">Hourly</option>
              <option value="15m">15 Minutes</option>
              <option value="5m">5 Minutes</option>
            </select>
          </div>
        </div>

        <div className="flex flex-col gap-4">
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Strategy (plain text)</label>
            <textarea
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white h-32 resize-none"
              placeholder="e.g. Buy when 20 EMA crosses above 50 EMA and RSI is below 70. Exit at 2% profit or 1% loss."
              value={strategyText}
              onChange={e => setStrategyText(e.target.value)}
            />
          </div>
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Or upload strategy (PDF / DOCX)</label>
            <input className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white" type="file" accept=".pdf,.docx" onChange={e => setFile(e.target.files[0])} />
          </div>
          <button
            className="mt-2 bg-green-500 hover:bg-green-400 text-black font-bold py-3 rounded disabled:opacity-50"
            onClick={runBacktest}
            disabled={loading || usageCount >= 5}
          >
            {loading ? "Running Backtest..." : usageCount >= 5 ? "Daily Limit Reached" : "Run Backtest"}
          </button>
        </div>
      </div>

      {error && (
        <div className="mt-6 bg-red-900 border border-red-500 text-red-200 px-4 py-3 rounded max-w-4xl">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-8 max-w-4xl">
          <h2 className="text-xl font-bold text-green-400 mb-4">Results</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: "Total Trades", value: result.total_trades },
              { label: "Win Rate", value: result.win_rate + "%" },
              { label: "Net P&L", value: "₹" + result.net_pnl },
              { label: "Max Drawdown", value: result.max_drawdown + "%" },
              { label: "Sharpe Ratio", value: result.sharpe_ratio },
              { label: "Profit Expectancy", value: "₹" + result.profit_expectancy },
              { label: "Winning Trades", value: result.winning_trades },
              { label: "Losing Trades", value: result.losing_trades },
            ].map((m, i) => (
              <div key={i} className="bg-gray-800 rounded p-4">
                <div className="text-gray-400 text-sm">{m.label}</div>
                <div className="text-white text-xl font-bold mt-1">{m.value}</div>
              </div>
            ))}
          </div>

          {result.equity_curve && result.equity_curve.length > 0 && (
            <div className="mt-6">
              <h3 className="text-lg font-semibold mb-3 text-gray-300">Equity Curve</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={result.equity_curve.map((v, i) => ({ trade: i, value: Math.round(v) }))}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="trade" stroke="#9CA3AF" label={{ value: "Trade #", position: "insideBottom", offset: -2, fill: "#9CA3AF" }} />
                  <YAxis stroke="#9CA3AF" tickFormatter={v => "₹" + v.toLocaleString()} />
                  <Tooltip formatter={v => "₹" + v.toLocaleString()} labelFormatter={l => "Trade " + l} contentStyle={{ backgroundColor: "#1F2937", border: "1px solid #374151" }} />
                  <Line type="monotone" dataKey="value" stroke="#22C55E" dot={false} strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {result.trades && result.trades.length > 0 && (
            <div className="mt-6">
              <h3 className="text-lg font-semibold mb-3 text-gray-300">Trade Log</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="text-gray-400 border-b border-gray-700">
                    <tr>
                      <th className="py-2 pr-4">Entry Date</th>
                      <th className="py-2 pr-4">Exit Date</th>
                      <th className="py-2 pr-4">Direction</th>
                      <th className="py-2 pr-4">Entry ₹</th>
                      <th className="py-2 pr-4">Exit ₹</th>
                      <th className="py-2 pr-4">P&L ₹</th>
                      <th className="py-2 pr-4">P&L %</th>
                      <th className="py-2 pr-4">Exit Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.trades.map((t, i) => (
                      <tr key={i} className="border-b border-gray-800">
                        <td className="py-2 pr-4">{t.entry_date}</td>
                        <td className="py-2 pr-4">{t.exit_date}</td>
                        <td className={`py-2 pr-4 font-semibold ${t.direction === "long" ? "text-green-400" : "text-red-400"}`}>{t.direction ?? "long"}</td>
                        <td className="py-2 pr-4">{t.entry_price}</td>
                        <td className="py-2 pr-4">{t.exit_price}</td>
                        <td className={`py-2 pr-4 font-semibold ${t.pnl > 0 ? "text-green-400" : "text-red-400"}`}>{t.pnl}</td>
                        <td className={`py-2 pr-4 ${t.pnl_pct > 0 ? "text-green-400" : "text-red-400"}`}>{t.pnl_pct}%</td>
                        <td className="py-2 pr-4 text-gray-400">{t.exit_reason}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}