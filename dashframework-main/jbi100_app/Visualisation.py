# ============================
# visualisations.py
# ============================

import plotly.express as px


# ==========================================
# Base class
# ==========================================

class Visualisation:
    """
    Abstract base class for all visualisation types.
    Each subclass implements:
      - required_fields()
      - render(df)
    """

    @classmethod
    def required_fields(cls):
        """
        Defines what parameters this visualisation needs in order to be created.
        The Create tab dynamically generates a form based on this.
        Must return a list of dicts:

            {
                "name": "x",
                "label": "X-axis attribute",
                "type": "attribute" | "attribute_optional" | "int" | "grouping"
            }

        """
        raise NotImplementedError

    def render(self, df):
        """
        Given a prepared dataframe (already filtered by the Data View),
        return a Plotly figure.
        """
        raise NotImplementedError


# ==========================================
# Scatter Plot
# ==========================================

class ScatterVis(Visualisation):

    @classmethod
    def required_fields(cls):
        return [
            {"name": "x", "label": "X-axis attribute", "type": "attribute"},
            {"name": "y", "label": "Y-axis attribute", "type": "attribute"},
            {"name": "color", "label": "Color attribute (optional)", "type": "attribute_optional"},
            {"name": "title", "label": "Title (optional)", "type": "text_optional"}
        ]

    def __init__(self, x, y, color=None, title=None):
        self.x = x
        self.y = y
        self.color = color
        self.title = title or "Scatter Plot"

    def render(self, df):
        fig = px.scatter(
            df,
            x=self.x,
            y=self.y,
            color=self.color,
            hover_name="Country",
            title=self.title,
        )
        fig.update_layout(title=self.title)
        return fig


# ==========================================
# Bar Chart
# ==========================================

class BarVis(Visualisation):

    @classmethod
    def required_fields(cls):
        return [
            {"name": "y", "label": "Y-axis value", "type": "attribute"},
            {"name": "x", "label": "Grouping variable", "type": "grouping"},
            {"name": "color", "label": "Color attribute (optional)", "type": "attribute_optional"},
            {"name": "title", "label": "Title (optional)", "type": "text_optional"},
        ]

    def __init__(self, x, y, color=None, title=None):
        self.x = x
        self.y = y
        self.color = color
        self.title = title or "Bar Chart"

    def render(self, df):
        fig = px.bar(
            df,
            x=self.x,
            y=self.y,
            color=self.color,
            hover_name="Country" if self.x == "Country" else None,
            title=self.title
        )
        fig.update_layout(title=self.title)
        return fig


# ==========================================
# Histogram
# ==========================================

class HistVis(Visualisation):

    @classmethod
    def required_fields(cls):
        return [
            {"name": "x", "label": "Attribute", "type": "attribute"},
            {"name": "bins", "label": "Number of bins", "type": "int", "default": 20},
            {"name": "title", "label": "Title (optional)", "type": "text_optional"},
        ]

    def __init__(self, x, bins=20, title=None):
        self.x = x
        self.bins = bins
        self.title = title or "Histogram"

    def render(self, df):
        fig = px.histogram(
            df,
            x=self.x,
            nbins=self.bins,
            title=self.title
        )
        fig.update_layout(title=self.title)
        return fig


# ==========================================
# Registry of available visualisations
# ==========================================

VIS_TYPES = {
    "scatter": ScatterVis,
    "bar": BarVis,
    "hist": HistVis,
}

