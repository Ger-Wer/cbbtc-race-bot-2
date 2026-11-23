# Momentum rider for cbBTC/USDC (CBBTC), 1-minute bars.
#
# Idea: the dev window is one big up-move followed by a long sideways
# stretch, and every fast mean-reversion / EMA-cross variant I tested
# bled money to whipsaw (the kit's ema-cross baseline: -114 USDC on
# 76 trades). So this bot does the opposite of clever:
#
#   * enter full size only when the trend is confirmed on two horizons
#     at once (30-bar return > 0.1% AND 120-bar return > 0.2%), which
#     keeps it out of flat chop;
#   * then ride the move and exit only on a trailing stop (2.5% below
#     the peak close since entry) or a hard stop (3% below entry cost).
#
# No exit on indicator crosses: in a sideways market they fire all the
# time and each round trip costs ~26 bps. One position at a time,
# long only, whole cash in, whole position out.
#
# Two harness behaviours need no code from us: orders decided on a
# warm-up batch are rejected by the harness (we return [] while
# warming up anyway), and orders decided on the last batch are
# rejected (after_end) while the open position is flattened at the
# last close — so the bot never has to special-case the end.
#
# Deterministic: integer arithmetic only, no clock, no randomness, no
# network, no environment. Two runs on the same bars give the same
# orders byte for byte.

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"

# Entry: 30-bar return above 0.1% and 120-bar return above 0.2%.
# Integer form: close * 1000 > close_30 * 1001  (return > 0.001)
#               close * 500  > close_120 * 501  (return > 0.002)
MOM_SHORT_BARS = 30
MOM_LONG_BARS = 120
MOM_SHORT_NUM = 1001  # return > 0.1%  -> close * 1000 > ref * 1001
MOM_SHORT_DEN = 1000
MOM_LONG_NUM = 501    # return > 0.2%  -> close * 500 > ref * 501
MOM_LONG_DEN = 500

# Exit: trailing stop 2.5% below the highest close since entry,
# hard stop 3% below the entry fill cost (approximated by the close
# of the bar on which we decided to buy; the fill is one bar later
# at the next open, so the stop is measured from that close).
TRAIL_NUM = 975  # close * 1000 < peak * 975  -> down more than 2.5%
TRAIL_DEN = 1000
HARD_NUM = 97    # close * 100 < cost * 97    -> down more than 3%
HARD_DEN = 100

MAX_SLIPPAGE_BPS = 200  # 2%: fills move ~0.3% on a normal bar


class Rider:
    def __init__(self):
        self.closes = []      # raw int closes, in order
        self.peak = None      # highest close since entry (raw int)
        self.cost = None      # close of the bar we decided to buy on

    def on_batch(self, state, batch):
        if state.warming_up:
            return []
        close = state.close(SYMBOL)
        if close is None:
            return []
        self.closes.append(close)
        holding = state.positions.get(SYMBOL)
        qty = holding.qty if holding is not None else 0

        if qty == 0:
            self.peak = None
            self.cost = None
            if len(self.closes) <= MOM_LONG_BARS:
                return []
            ref_short = self.closes[-1 - MOM_SHORT_BARS]
            ref_long = self.closes[-1 - MOM_LONG_BARS]
            up_short = close * MOM_SHORT_DEN > ref_short * MOM_SHORT_NUM
            up_long = close * MOM_LONG_DEN > ref_long * MOM_LONG_NUM
            if up_short and up_long and state.cash >= 1_000_000:
                self.cost = close
                self.peak = close
                return [{
                    "side": "buy",
                    "symbol": SYMBOL,
                    "notional_quote_units": state.cash,
                    "max_slippage_bps": MAX_SLIPPAGE_BPS,
                }]
            return []

        # In a position: ride it, exit only on the stops.
        if self.peak is None:
            self.peak = close
        if close > self.peak:
            self.peak = close
        if self.cost is None:
            self.cost = close
        trail_hit = close * TRAIL_DEN < self.peak * TRAIL_NUM
        hard_hit = close * HARD_DEN < self.cost * HARD_NUM
        if trail_hit or hard_hit:
            self.peak = None
            self.cost = None
            return [{
                "side": "sell",
                "symbol": SYMBOL,
                "qty": qty,
                "max_slippage_bps": MAX_SLIPPAGE_BPS,
            }]
        return []


def main():
    rider = Rider()
    makefun_bars.run(rider.on_batch)


if __name__ == "__main__":
    main()
