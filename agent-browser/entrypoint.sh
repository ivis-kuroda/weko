#!/usr/bin/env bash
set -e

if [ -n "${DISPLAY:-}" ] && ! pgrep -f "Xvfb ${DISPLAY}" >/dev/null 2>&1; then
    Xvfb "${DISPLAY}" -screen 0 "${XVFB_SCREEN:-1280x720x24}" >/tmp/xvfb.log 2>&1 &
fi

exec "$@"
