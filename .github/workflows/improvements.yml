name: Improvements test

# Tests three changes on the full history: cash when bonds fall too, filling
# empty slots sooner, and the market switch speed. Results: docs/IMPROVEMENTS.md

on:
  workflow_dispatch:

permissions:
  contents: write

concurrency:
  group: improvements
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
        run: python scripts/improvements_test.py

      - name: Commit
        if: always()
        run: |
          bash scripts/commit_push.sh "improvements test $(date -u +%Y-%m-%d)" \
            docs/IMPROVEMENTS.md data/improvements.json
