# Global Stock Market Dashboard

**Short description**
A responsive single-page dashboard (Streamlit) that visualizes global stock price data (monthly variation, top & bottom companies, locations on a map, and animated price fluctuations). The app can load your own `World Stock Prices (Daily Updating)` CSV from Kaggle or use a built-in sample for demonstration.

---

## Features

* Monthly price variation (bar chart)
* Top **K** companies by average close (doughnut / pie)
* Bottom **K** companies by average close (doughnut / pie)
* Map (Leaflet/Folium) to show HQ locations of top companies
* Animated chart showing daily fluctuations for top N companies
* Filters: month and industry
* CSV upload support and filtered data download

---

## Dataset

This project expects the **World Stock Prices (Daily Updating)** dataset from Kaggle.
📌 Dataset URL: [https://www.kaggle.com/datasets/nelgiriyewithana/world-stock-prices-daily-updating](https://www.kaggle.com/datasets/nelgiriyewithana/world-stock-prices-daily-updating)

It contains daily historical stock data per brand including Date, Open, High, Low, Close, Volume, Dividends, Stock Splits, Brand_Name, Ticker, Industry_Tag, Country, and location coordinates (lat/lon). Use this dataset (or any similarly structured CSV) as input for the dashboard.

If you prefer to download from the command line (Kaggle CLI):

```bash
# requires kaggle CLI configured (https://www.kaggle.com/docs/api)
kaggle datasets download -d nelgiriyewithana/world-stock-prices-daily-updating
unzip world-stock-prices-daily-updating.zip
```

---

## Prerequisites

* Python 3.9+ (recommended)
* pip
* (Optional) Virtual environment: `venv`, `virtualenv`, or `conda`

---

## Installation (quick)

```bash
# create and activate venv (optional but recommended)
python -m venv .venv
# on Linux/macOS
source .venv/bin/activate
# on Windows (PowerShell)
.venv\Scripts\Activate.ps1

# install required packages
pip install streamlit pandas plotly folium streamlit-folium pydeck
```

---

## Project files (example)

```
project-root/
├─ app.py                # Streamlit app (main)
├─ stock-dashboard.html  # Static HTML version of dashboard (Chart.js version)
├─ check_data.ipynb      # Jupyter notebook for data exploration
├─ requirements.txt      # (optional) pinned dependencies
├─ README.md             # This file
├─ data/
│  └─ world_stock.csv    # place your Kaggle CSV here (or upload in UI)
└─ assets/               # (optional) logos, icons, additional resources
```

**Notes**

* `app.py` is the Streamlit application that reads the CSV (or uses sample data) and renders charts & map.
* `stock-dashboard.html` is the earlier Chart.js-based static version (kept for alternative).
* `check_data.ipynb` is a helper notebook for checking/cleaning the dataset.

---
