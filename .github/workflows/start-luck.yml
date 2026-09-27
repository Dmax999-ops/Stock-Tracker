name: Start-date luck

# Starts the strategy on every week since 2000 and follows each start for
# 10 and 5 years (GBP 10,000, Trading 212 costs): one start vs four starts a
# week apart. Results: docs/START_LUCK.md

on:
  workflow_dispatch:

permissions:
  contents: write

concurrency:
  group: start-luck
  cancel-in-progress: false

jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 180
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: pip
      - name: Install dependencies
        run: pip install -r requirements.txt requests lxml pyyaml pyarrow

      - name: Rebuild price panel if absent
        run: |
          if [ ! -f data/prices.parquet ]; then
            python scripts/fetch_universe.py --config config/universe.yml --out data/
          fi

      - name: Run the test
        env:
          POT_GBP: '10000'
          BROKER: t212
        run: python scripts/start_luck.py

      - name: Commit
        if: always()
        run: |
          bash scripts/commit_push.sh "start-date luck $(date -u +%Y-%m-%d)" \
            docs/START_LUCK.md data/start_luck.json data/start_luck_10y.csv data/start_luck_5y.csv
