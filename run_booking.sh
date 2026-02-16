#!/bin/zsh

SCRIPT_DIR="/Users/I568712/Dev/uni/unisport-automation"
LOG_FILE="${SCRIPT_DIR}/booking.log"

echo "=== Booking attempt: $(date) ===" >> "$LOG_FILE"
cd "$SCRIPT_DIR"
/opt/homebrew/bin/pipenv run python book_course.py >> "$LOG_FILE" 2>&1
echo "" >> "$LOG_FILE"
