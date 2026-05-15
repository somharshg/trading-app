# Strategy Backtester

A web app to backtest trading strategies against NSE/BSE historical data using plain English input.

## Features
- Plain text strategy input (powered by Groq AI)
- PDF and Word document upload
- EMA, RSI indicator strategies
- Range Breakout strategies (CDH, CDL, PDH, PDL)
- Performance analytics: Win rate, P&L, Sharpe ratio, Drawdown

## Setup

### Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install fastapi uvicorn yfinance pandas numpy python-multipart pypdf2 python-docx groq python-dotenv
Create a .env file with: GROQ_API_KEY=your_key_here
uvicorn main:app --reload

### Frontend
cd frontend
npm install
npm run dev

## Usage
1. Enter NSE stock symbol (e.g. RELIANCE, TCS)
2. Set capital, period, interval
3. Type your strategy in plain English
4. Click Run Backtest