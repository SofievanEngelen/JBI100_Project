# Visualization Tools for Model United Nations

An interactive data visualization tool designed to support **Model United Nations (MUN)** delegates in building data-driven country profiles and making defensible cross-country comparisons.

This project was developed as part of the **JBI100 – Visualization** course at Eindhoven University of Technology.

---

##  Project Overview

Preparing for MUN debates requires quickly understanding and comparing countries across many domains such as economy, demographics, environment, and governance. Static tables and textual summaries make this difficult under time pressure.

This tool provides an **integrated interactive workspace** that enables users to:
- Explore country-level indicators visually
- Compare countries across multiple attributes
- Identify regional patterns, trade-offs, outliers, and potential allies
- Support arguments with clear, explainable visual evidence

The system is built using **Python and Dash**, combining coordinated views such as maps, parallel coordinates, and distribution plots into a single interface :contentReference[oaicite:0]{index=0}.

---

##  Key Features

- **Choropleth World Map**
  - Visualize indicators geographically
  - Hover for precise values
  - Click countries to select them for comparison

- **Parallel Coordinates Plot (PCP)**
  - Compare up to 8 indicators simultaneously
  - Brush ranges on axes to filter countries
  - Reorder axes and highlight selections

- **Auxiliary Plots (Configurable)**
  - Scatterplots (with lasso brushing)
  - Histograms / density plots
  - Violin + box plots for distribution comparison
  - Radar charts for focused multi-attribute comparison

- **Brushing & Linking**
  - Selections propagate across all views
  - Enables fast exploratory analysis

- **Semantic Scaling**
  - Switch reference context between **global**, **continent**, and **region**

- **Dark Mode**
  - Improves readability and reduces visual fatigue

---

##  Data Source

The tool uses country-level indicators derived from the **CIA World Factbook (2024–2025)**, compiled via Kaggle.

### Data preprocessing includes:
- Harmonized country names
- Removal of non-UN member states
- Derived indicators (e.g. GDP per capita, CO₂ per capita, trade openness)
- Optional log scaling for skewed attributes

Missing values are **not imputed**; countries without valid data are excluded only from the relevant visualizations to avoid misleading comparisons.

---

##  Supported Use Cases

The tool is specifically designed to support typical MUN preparation tasks:

- Country profile briefing
- Regional benchmarking
- Multi-criteria trade-off analysis
- Ally and contrast-case discovery
- Outlier detection for evidence-based critique

Example use cases are described in detail in the project report, including:
- Identifying regional disparities
- Analyzing high CO₂-per-capita countries using multivariate profiles :contentReference[oaicite:1]{index=1}

---

## ️ Implementation

- **Language:** Python  
- **Framework:** Dash (Plotly)
- **Architecture:**
  - Python preprocessing layer for cleaning and transforming data
  - Dash callbacks for interaction, brushing, and linking
  - Single integrated dashboard layout

---

##  Running the Project

> ️ Instructions may need adjustment depending on your local setup.

1. Clone the repository:
   ```bash
   git clone https://github.com/SofievanEngelen/JBI100_Project.git
   cd JBI100_Project
   ```
2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Run the Dash application:
```bash
python app.py
```

4. Open the local server (usually):
```bash
http://127.0.0.1:8050/
```
##  Authors

- Sofie van Engelen
- Jordi van den Berg
- Jiawen Zhang
- Shuhan Cao

## Report

The full design rationale, task analysis, and evaluation are documented in the accompanying project report (included in this repository).

## References

Munzner, T. Visualization Analysis and Design

United Nations. Model United Nations

CIA World Factbook (2024–2025)

## Future Work

Potential extensions include:
- Scatterplot matrix for multivariate correlation analysis
- Improved handling of extreme outliers
- Additional indicators and domains
- Enhanced guidance for indicator selection and comparable countries