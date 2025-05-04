#!/bin/bash
cd /Users/junhaotee/Desktop/Side_projects/FinanceWebScrapper
# Set PATH to include Homebrew binaries
export PATH="/opt/homebrew/bin:$PATH"
echo"Path is : $PATH"
source venv/bin/activate

# Read values from config.json and pass them to the Python script
TICKERS=$(jq -r '.tickers | join(",")' config.json)
SOURCES=$(jq -r '.sources | join(" ")' config.json)
FORMAT=$(jq -r '.format' config.json)
OUTPUT_DIR=$(jq -r '.output_dir' config.json)
EMAIL=$(jq -r '.email' config.json)
SUMMARY=$(jq -r '.summary' config.json)
SAVEREPORT=$(jq -r '.saveReports' config.json)

# Build command based on config
CMD="python main.py --tickers $TICKERS --sources $SOURCES --format $FORMAT --output-dir $OUTPUT_DIR --email $EMAIL --saveReports $SAVEREPORT"

# Add optional flags
if [ "$SUMMARY" = "true" ]; then
  CMD="$CMD --summary"
fi

# Execute the command
echo "Running: $CMD"
eval $CMD
