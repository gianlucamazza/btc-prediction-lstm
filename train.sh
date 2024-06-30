#!/bin/bash

if [ -z "$BASH_VERSION" ]; then
  echo "This script requires Bash. Please run with Bash."
  exit 1
fi

# Set ticker and date range
declare -A TICKER_DATES=(
  ["GLD"]="2000-01-01"
  ["BTC"]="2010-01-01"
)
END_DATE="2024-06-29"

# Run cleanup script
bash cleanup.sh

# Loop through each ticker
for TICKER in "${!TICKER_DATES[@]}"; do
  echo "Processing $TICKER"

  START_DATE="${TICKER_DATES[$TICKER]}"

  # Prepare the data
  python src/data/data_preparation.py --ticker="$TICKER" --start_date="$START_DATE" --end_date="$END_DATE"

  # Setup feature engineering
  python src/data/feature_engineering.py --ticker="$TICKER"

  # Train the model
  python src/training/train_model.py --ticker="$TICKER"
done
