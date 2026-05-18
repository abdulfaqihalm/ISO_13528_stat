#!/bin/bash
# Double-click this file to launch the Algorithm A web app in your browser.
# (On first run, macOS may ask you to allow execution — click "Open".)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Try to find streamlit in common locations
STREAMLIT=""
for candidate in \
    "$SCRIPT_DIR/.venv/bin/streamlit" \
    "$HOME/anaconda3/bin/streamlit" \
    "$HOME/miniconda3/bin/streamlit" \
    "$(command -v streamlit 2>/dev/null)"
do
    if [ -x "$candidate" ]; then
        STREAMLIT="$candidate"
        break
    fi
done

if [ -z "$STREAMLIT" ]; then
    osascript -e 'display alert "streamlit not found" message "Please install it first:\n\n  pip install streamlit\n\nThen try again."'
    exit 1
fi

# Open a terminal window that keeps visible so users can see the URL
osascript <<EOF
tell application "Terminal"
    activate
    do script "cd '$SCRIPT_DIR' && '$STREAMLIT' run app.py"
end tell
EOF
