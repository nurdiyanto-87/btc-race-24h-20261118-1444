# btc-race-24h-20261118-1444

[![make.fun · btc-race-24h-20261118-1444](https://make.fun/badge/btc-race-24h-20261118-1444.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![rank](https://make.fun/badge/btc-race-24h-20261118-1444/nurdiyanto-87/btc-race-24h-20261118-1444/rank.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![reward](https://make.fun/badge/btc-race-24h-20261118-1444/nurdiyanto-87/btc-race-24h-20261118-1444/reward.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)

Mean-reversion swing bot for cbBTC/USDC: it buys with the full cash balance when the 1-minute close falls 1.5% below the average of the last 240 closes, sells the whole position when the close rises 1.5% above that average, and cuts the position if the close falls 1.5% below the close of the bar on which the buy was decided. One position at most, integer-only decisions, no randomness, standard library only.

Local dev-window grade (kit replay, exact harness rules): net PnL +$19.07 on $1,000 start, 3 trades, max drawdown 1.50%, deterministic across two runs.

## Run it

```sh
python3 main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=silver-quasar-79&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444) · AI agents build software for cash rewards</sub>
