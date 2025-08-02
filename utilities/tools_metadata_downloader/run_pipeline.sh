#!/bin/bash

set -e

echo "Starting Galaxy tool download + validation pipeline..."

# Step 1: Run downloader
echo "Running downloader..."
python tool_downloader.py

# Step 2: Get the most recent JSON output file
echo "Locating latest downloaded tool file..."
LATEST_FILE=$(ls -t galaxy_instance_tools_*.json | head -n 1)

if [[ -z "$LATEST_FILE" ]]; then
  echo "❌ No tool file found. Exiting."
  exit 1
fi

echo "✅ Found latest tool file: $LATEST_FILE"

# Step 3: Run validator on the latest file
echo "🧪 Validating $LATEST_FILE..."
python tool_schema_validator.py "$LATEST_FILE"

# Step 4 (optional): Automatically move validated file to agents/data
VALIDATED_DIR="agents/data"
mkdir -p "$VALIDATED_DIR"

# Optional: Ask user if they want to move
read -p "📦 Do you want to move the validated file to $VALIDATED_DIR? [y/N]: " move_answer
if [[ "$move_answer" =~ ^[Yy]$ ]]; then
  echo "📁 Moving validated file to $VALIDATED_DIR"
  # Move only if validator output is known. If validator writes a fixed name, use it here.
  # Otherwise, ask validator.py to echo it to a file, e.g., validator_output_path.txt
  VALIDATED_FILE=$(ls -t *.json | grep -v galaxy_instance_tools_ | head -n 1)
  mv "$VALIDATED_FILE" "$VALIDATED_DIR"
  echo "✅ Moved to $VALIDATED_DIR/$VALIDATED_FILE"
else
  echo "⚠️ Skipping move. You can do it manually."
fi

echo "Pipeline completed! 🎉"
