# jbi100_app/main.py
from dash import Dash

app = Dash(
    __name__,
    suppress_callback_exceptions=True,
)

app.title = "JBI100 Dashboard"
