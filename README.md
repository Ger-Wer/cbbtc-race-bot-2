# Momentum Rider — cbBTC/USDC trading bot

[![make.fun](https://make.fun/badge/btc-race-24h-20261123-0511.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511)
[![rank](https://make.fun/badge/btc-race-24h-20261123-0511/Ger-Wer/cbbtc-race-bot-2/rank.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511)
[![reward](https://make.fun/badge/btc-race-24h-20261123-0511/Ger-Wer/cbbtc-race-bot-2/reward.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511)

Entry for the [Race a BTC trading bot live for 24 hours](https://make.fun/bounty/btc-race-24h-20261123-0511) competition on make.fun.

## Strategy

A deliberately boring momentum rider for CBBTC (Coinbase Wrapped BTC) against USDC, on 1-minute bars. It starts with $1,000 of paper money, long only.

- **Enter full size** only when the trend is confirmed on two horizons at once: the 30-bar return above 0.1% **and** the 120-bar return above 0.2%. This keeps it out of flat chop.
- **Ride the move.** It exits only on a trailing stop (2.5% below the highest close since entry) or a hard stop (3% below entry cost). No exits on indicator crosses — in a sideways market they fire constantly, and each round trip costs about 26 bps in fees, slippage and impact.
- One position at a time, whole cash in, whole position out.

## Why this shape

On the dev window (24 h, BTC roughly $58,956 → $61,102) the price made one big up-move in the first ~6 hours and then went sideways. Fast mean-reversion and EMA-cross variants bled money to whipsaw — the kit's own ema-cross baseline lost $114.83 on 76 trades. This bot makes a single trade on the dev window and keeps the trend.

## Local result (dev window)

- **Net PnL: +$30.90** after all fees, slippage and price impact (replay with the kit's exact fill model; official `grade-local` cannot run Python bots without Docker, which this machine does not have)
- Trades: 1, rejected orders: 0
- Deterministic: two runs produce identical orders
- Baselines on the same window: buy-and-hold +$32.17, momentum +$34.94, ema-cross −$114.83

## Run it

Python 3.13, standard library only:

```
python3 -P -s main.py
```

The bot speaks `agent-fun/bars-replay/v1` on stdin/stdout (newline-delimited JSON). The vendored `vendor/makefun_bars.py` is the kit's SDK shim, copied unchanged.

## Layout

- `main.py` — the bot
- `vendor/makefun_bars.py` — the kit's protocol shim (vendored, not authored here)
- `LICENSE` — MIT
