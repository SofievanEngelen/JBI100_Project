from __future__ import annotations

import json
from datetime import datetime, timezone

from dash import Input, Output, callback


@callback(
    Output("debug-pcp-brush-log", "children"),
    Input("pcp-brush-store", "data"),
    prevent_initial_call=True,
)
def log_pcp_brush_store(data):
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")

    print("\n" + "=" * 90)
    print(f"[pcp-brush-store WRITE] {ts}")
    print(json.dumps(data, indent=2, default=str, ensure_ascii=False))
    print("=" * 90 + "\n")

    # Dash needs an Output; we store a timestamp (invisible)
    return ts
