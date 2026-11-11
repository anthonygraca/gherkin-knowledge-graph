#!/bin/sh
# Network-denied reproduction of the offline test suite (run under `unshare -rn`).
PY="/home/anthonygraca/CSU Fullerton Dropbox/Anthony Graca/cpsc-583-knowledge-representation/project/gherkin-knowledge-graph/backend/.venv/bin/python"
cd "/home/anthonygraca/CSU Fullerton Dropbox/Anthony Graca/cpsc-583-knowledge-representation/project/gherkin-knowledge-graph" || exit 9
"$PY" -c 'import socket; socket.create_connection(("1.1.1.1", 443), timeout=3)' && echo "NET-ALLOWED(BAD)" || echo "NET-DENIED-OK"
"$PY" -m pytest backend/tests -q
