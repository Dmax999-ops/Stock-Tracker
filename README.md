# quant-signals

A state classifier for a small equity portfolio. Runs free on GitHub Actions,
publishes to GitHub Pages, and keeps a tamper-evident log of every call it makes.

**It is not a predictor.** It sorts each holding into one of six states, two of
which carry measurable statistical weight. The other four are reported so you can
watch them decay, not so you can trade them.

---

## What the evidence actually says

Trained on 498 S&P constituents, 461,930 stock-days, daily bars:

| State | 1-month forward | t vs universe | Verdict |
|---|---|---|---|
| **CAPITULATION** | +1.57% | **+4.35** | **Tradeable — buy** |
| FALLING | +1.19% | +1.81 | Not tradeable |
| COOLING | +0.94% | +0.64 | Not tradeable |
| STEADY | +0.82% | −0.58 | Not tradeable |
| STRONG | +0.80% | −0.86 | Not tradeable |
| **TOPPING** | +0.41% | **−3.82** | **Tradeable — reduce** |

Two states out of six. Everything in between is noise, and the threshold (|t| ≥ 2.5)
was fixed before the results were seen.

### Three things that are easy to get wrong

**"Strong" is not a buy.** A stock that is extended inside an uptrend tested as
nothing (t = −0.86). It feels like the best state and isn't.

**"Cold" is not a buy either.** General weakness (COOLING) has no edge. Only
*capitulation* — three of five indicators simultaneously in their bottom decile —
carries signal. Most cold readings are stocks that keep falling.

**Capitulation is territory, not timing.** Median signal fires ~7 weeks before the
low, with a median further fall of ~12%. Ladder in over three tranches. If you buy
the whole position on the first signal you will usually be underwater before you
are right.

---

## The survivorship problem — read this before trusting any number above

The training universe is index membership at the *end* of the sample. Every company
that capitulated and then went bankrupt or was delisted is **missing from the data**.

Buy-the-dip looks excellent when the dips that never recovered have been deleted.
The CAPITULATION result is therefore an **optimistic ceiling**, and it is optimistic
in exactly the direction that would cost you money.

`data/manifest.json` reports how many tickers stopped updating (a proxy for
delisting). If that number is near zero, the universe is survivor-only.

Fixing this properly means historical constituent lists or a paid survivorship-free
source. See the notes in `config/universe.yml`.

---

## Layout

```
.github/workflows/
  fetch-universe.yml    weekly: pull history, retrain, commit evidence
  daily-signals.yml     weekdays: classify holdings, write signals.json
quant/
  states.py             the classifier
  indicators.py         trend / momentum / volatility / reversion
  data.py               adjustment + bad-tick repair
  metrics.py            performance stats
scripts/
  fetch_universe.py     universe pull, with survivorship reporting
  train_states.py       retrain + evidence table + t-statistics
  daily_signals.py      per-holding call, appends to the prediction log
config/
  holdings.yml          your positions — the TEST set, never used for fitting
  universe.yml          the training universe
docs/
  index.html            dashboard (GitHub Pages)
  signals.json          machine-readable output
data/
  prices.parquet        price history
  state_evidence.json   the evidence table, committed each run
  signal_history.csv    every call ever made, append-only
```

---

## Setup

1. Create the repo and push this tree.
2. **Settings → Actions → General → Workflow permissions → Read and write.**
   Without this the commit steps fail.
3. **Settings → Pages → Source: Deploy from branch → `main` / `docs`.**
4. Run **Fetch universe** manually once (Actions tab → Run workflow). Takes
   20–40 minutes for a full history pull.
5. Daily signals runs itself on weekdays at 06:00 UTC.

### Optional: alerts

Set a repo secret `NTFY_TOPIC` to a random string, subscribe to that topic in the
[ntfy](https://ntfy.sh) app, and you get a push **only when a holding changes
state**. Silence is deliberate — a daily "nothing happened" notification trains
you to ignore the one that matters.

### Cost

About 60 Actions minutes a month against a free allowance of 2,000 (private) or
unlimited (public). Pages hosting is free.

**One gotcha:** GitHub disables scheduled workflows after 60 days of repository
inactivity. Both jobs commit on every run, which keeps the schedule alive.

---

## Reading it back

`docs/signals.json` is fetchable at:

```
https://raw.githubusercontent.com/<user>/<repo>/main/docs/signals.json
```

That URL is how Claude reads the current state without any credential ever being
shared.

---

## The prediction log

`data/signal_history.csv` is appended on every run and committed. Git makes it
tamper-evident — you cannot quietly revise what the system said last month.

After twelve months it is the only genuinely out-of-sample record you will have.
Everything above it is simulation. This is the file that can prove the system
wrong, which is precisely why it exists.

---

## What was tested and rejected

So nobody rebuilds them:

| Rejected | Result |
|---|---|
| RSI 30/70, Bollinger reversion | −15% to −18%/yr across 6 stocks |
| MACD, Donchian/Turtle, Chandelier, Ichimoku, Faber, Parabolic SAR | all negative |
| Breakouts, volume-confirmed breakouts, squeeze breakouts, trendlines | 0–2 wins in 48 tests |
| Connors RSI(2) and short-horizon dip buying | −20% to −26%/yr; worse the faster they trade |
| Selling on peak signals | peaks are undetectable — 1.9× lift, 20 weeks early, 83% of upside forgone |
| Every standard re-entry signal after a drawdown | all 10 lost to simply holding |
| Long/short CAPITULATION vs TOPPING, monthly | 14.8% gross → **1.3% after costs** |

The finding that held across everything: **less trading beat more trading,
monotonically.** The long-only, low-turnover configuration is the only one where
the edge survives friction.

---

Signals, not advice. Nothing here is a recommendation to buy or sell anything.
