#!/bin/sh
# Export the deck to PDF: one 1280x720 page per slide.
# Uses any installed Chromium-based browser in headless mode.
set -e
cd "$(dirname "$0")"
cargo run

for b in \
  "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" \
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" \
  "/Applications/Chromium.app/Contents/MacOS/Chromium"; do
  if [ -x "$b" ]; then
    "$b" --headless --disable-gpu --no-pdf-header-footer \
      --virtual-time-budget=3000 \
      --print-to-pdf=quic-talk.pdf "file://$PWD/docs/index.html"
    exit 0
  fi
done
echo "no Chromium-based browser found" >&2
exit 1
