#!/usr/bin/env python3
"""Mean-reversion swing bot for the cbBTC/USDC 1-minute bars replay.

The bot holds at most one long position. It spends the full cash balance
when the latest close prints BAND_BPS below the simple moving average of
the last SMA_LEN closes, sells the whole position when the close prints
BAND_BPS above that average, and cuts the position early if the close falls
STOP_BPS below the close of the bar on which the buy was decided. No
orders are placed until MIN_HISTORY closes have been seen, so the average
is never built on a handful of bars.

The bot speaks agent-fun/bars-replay/v1 directly: newline-delimited JSON on
stdin (hello, one batch per minute, done) and exactly one reply per batch
on stdout. Every decision uses integer arithmetic on the bars' own integer
prices, with no clock, no environment reads and no randomness, so two runs
on the same data answer byte for byte alike. Standard library only.
"""

import json
import sys
from collections import deque

SYMBOL = "CBBTC"
SMA_LEN = 240            # closes feeding the moving average
MIN_HISTORY = 60         # closes needed before the first order
BAND_BPS = 150           # 1.5% below/above the average to buy/sell
STOP_BPS = 150           # 1.5% below the entry-decision close to cut
MAX_SLIPPAGE_BPS = 100   # covers the 1-minute gap plus slippage and impact
BPS = 10_000


class SwingBot:
    """One long position at a time, driven by closes vs. their SMA."""

    def __init__(self, hello):
        self.closes = deque(maxlen=SMA_LEN)
        self.closes_sum = 0
        self.bars_seen = 0
        self.last_bar_t = -1
        self.warmup_bars = hello.get("warmup_bars", 0)
        self.min_notional = int(hello["fees"]["min_notional_quote_units"])
        self.next_id = 1
        # Close of the bar on which the current buy was decided; the stop
        # is measured from it, not from the fill price.
        self.entry_close = None
        # After a stop-out, the close is usually still deep below the
        # average, so the buy rule would fire again on the next bar and
        # churn fees re-entering the same falling move. Skip buys until
        # one fresh bar after the stop.
        self.stop_cooldown = 0

    def on_batch(self, batch):
        seq = batch["seq"]
        account = batch["account"]
        cash = int(account["cash_quote_units"])
        held_qty = 0
        for pos in account["positions"]:
            if pos["symbol"] == SYMBOL:
                held_qty = int(pos["qty"])
        if held_qty <= 0:
            self.entry_close = None

        # Fold this batch's bar in, if it carries a new one for our symbol.
        new_close = None
        for bar in batch["bars"]:
            if bar["symbol"] == SYMBOL and int(bar["t"]) > self.last_bar_t:
                new_close = int(bar["c"])
                self.last_bar_t = int(bar["t"])
        if new_close is not None:
            if len(self.closes) == SMA_LEN:
                self.closes_sum -= self.closes[0]
            self.closes.append(new_close)
            self.closes_sum += new_close
            self.bars_seen += 1

        orders = []
        warming_up = self.warmup_bars > 0 and seq < self.warmup_bars
        if (
            new_close is not None
            and not warming_up
            and self.bars_seen >= MIN_HISTORY
        ):
            n = len(self.closes)
            avg_sum = self.closes_sum
            if held_qty <= 0:
                # Buy: close BAND_BPS below the average, spending all cash.
                below_band = (
                    new_close * n * BPS < avg_sum * (BPS - BAND_BPS)
                )
                cooled_down = self.bars_seen > self.stop_cooldown
                if below_band and cooled_down and cash >= self.min_notional:
                    orders.append(
                        {
                            "side": "buy",
                            "client_id": self._client_id(),
                            "symbol": SYMBOL,
                            "notional_quote_units": str(cash),
                            "max_slippage_bps": MAX_SLIPPAGE_BPS,
                        }
                    )
                    self.entry_close = new_close
            else:
                # Sell: close BAND_BPS above the average, or STOP_BPS under
                # the close of the bar on which the buy was decided.
                above_band = (
                    new_close * n * BPS > avg_sum * (BPS + BAND_BPS)
                )
                stopped = (
                    self.entry_close is not None
                    and new_close * BPS
                    < self.entry_close * (BPS - STOP_BPS)
                )
                if above_band or stopped:
                    if stopped:
                        self.stop_cooldown = self.bars_seen + 1
                    orders.append(
                        {
                            "side": "sell",
                            "client_id": self._client_id(),
                            "symbol": SYMBOL,
                            "qty": str(held_qty),
                            "max_slippage_bps": MAX_SLIPPAGE_BPS,
                        }
                    )
        return orders

    def _client_id(self):
        cid = "o%d" % self.next_id
        self.next_id += 1
        return cid


def main():
    bot = None
    out = sys.stdout
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        msg = json.loads(line)
        kind = msg.get("type")
        if kind == "hello":
            bot = SwingBot(msg)
        elif kind == "batch":
            # The harness always sends hello first; stay alive on the wire
            # even if a batch somehow arrives before it.
            orders = bot.on_batch(msg) if bot is not None else []
            reply = {"type": "reply", "seq": msg["seq"], "orders": orders}
            out.write(json.dumps(reply, separators=(",", ":")) + "\n")
            out.flush()
        elif kind == "done":
            return


if __name__ == "__main__":
    main()
