# app.py
"""
Streamlit Stock Dashboard
Features:
1. Monthly price variation (Bar)
2. Top 10 companies (current month avg) (Pie)
3. Least 10 companies (current month avg) (Pie)
4. Map showing location of top 10 company listings
5. Animated chart to show fluctuations in stock price

Usage:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
from streamlit_folium import st_folium
import folium

st.set_page_config(layout="wide", page_title="Global Stock Market Dashboard 📈")

# -----------------------
# Helpers & sample data
# -----------------------
@st.cache_data
def generate_sample_data():
    """Create a small realistic sample dataset if user doesn't upload one."""
    rng = pd.date_range(start="2024-10-01", periods=31, freq="D")
    companies = [
        {"Brand_Name":"Apple Inc.","Ticker":"AAPL","Industry_Tag":"Technology","Country":"USA","lat":37.3318,"lon":-122.0296},
        {"Brand_Name":"Microsoft Corp.","Ticker":"MSFT","Industry_Tag":"Technology","Country":"USA","lat":47.6062,"lon":-122.3321},
        {"Brand_Name":"Amazon.com Inc.","Ticker":"AMZN","Industry_Tag":"Retail","Country":"USA","lat":47.6062,"lon":-122.3321},
        {"Brand_Name":"Alphabet Inc.","Ticker":"GOOGL","Industry_Tag":"Technology","Country":"USA","lat":37.4220,"lon":-122.0841},
        {"Brand_Name":"Tesla Inc.","Ticker":"TSLA","Industry_Tag":"Automotive","Country":"USA","lat":37.3947,"lon":-122.1498},
        {"Brand_Name":"NVIDIA Corp.","Ticker":"NVDA","Industry_Tag":"Technology","Country":"USA","lat":37.3708,"lon":-121.9959},
        {"Brand_Name":"Meta Platforms","Ticker":"META","Industry_Tag":"Technology","Country":"USA","lat":37.4850,"lon":-122.1473},
        {"Brand_Name":"JPMorgan Chase","Ticker":"JPM","Industry_Tag":"Finance","Country":"USA","lat":40.7128,"lon":-74.0060},
        {"Brand_Name":"Johnson & Johnson","Ticker":"JNJ","Industry_Tag":"Healthcare","Country":"USA","lat":40.4968,"lon":-74.4444},
        {"Brand_Name":"Walmart Inc.","Ticker":"WMT","Industry_Tag":"Retail","Country":"USA","lat":36.3729,"lon":-94.2088},
        {"Brand_Name":"ExxonMobil","Ticker":"XOM","Industry_Tag":"Energy","Country":"USA","lat":32.8893,"lon":-97.0362},
        {"Brand_Name":"Pfizer Inc.","Ticker":"PFE","Industry_Tag":"Healthcare","Country":"USA","lat":40.7128,"lon":-74.0060},
        {"Brand_Name":"Chevron Corp.","Ticker":"CVX","Industry_Tag":"Energy","Country":"USA","lat":37.9265,"lon":-122.5270},
        {"Brand_Name":"Home Depot","Ticker":"HD","Industry_Tag":"Retail","Country":"USA","lat":33.7490,"lon":-84.3880},
        {"Brand_Name":"Mastercard Inc.","Ticker":"MA","Industry_Tag":"Finance","Country":"USA","lat":41.0382,"lon":-73.5413},
    ]
    rows = []
    for comp in companies:
        base = np.random.uniform(50, 800)
        for d in rng:
            daily_noise = np.random.normal(0, base*0.02)
            openp = base + daily_noise + np.random.uniform(-3, 3)
            high = openp + abs(np.random.normal(0, base*0.01)) + np.random.uniform(0, 5)
            low = openp - abs(np.random.normal(0, base*0.01)) - np.random.uniform(0, 5)
            close = openp + np.random.normal(0, base*0.01)
            volume = int(np.random.uniform(1e5, 5e7))
            rows.append({
                "Date": d,
                "Open": round(openp, 2),
                "High": round(high, 2),
                "Low": round(low, 2),
                "Close": round(close, 2),
                "Volume": volume,
                "Dividends": 0.0,
                "Stock Splits": 0.0,
                "Brand_Name": comp["Brand_Name"],
                "Ticker": comp["Ticker"],
                "Industry_Tag": comp["Industry_Tag"],
                "Country": comp["Country"],
                "lat": comp["lat"],
                "lon": comp["lon"]
            })
    df = pd.DataFrame(rows)
    return df

def try_parse_dates(df):
    for c in df.columns:
        if c.lower() in ("date", "datetime", "day"):
            try:
                df["Date"] = pd.to_datetime(df[c])
                return df
            except Exception:
                pass
    # Try to coerce if 'Date' column exists but not datetime
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    return df

# -----------------------
# UI - Sidebar
# -----------------------
st.sidebar.title("Data & Filters")
uploaded = st.sidebar.file_uploader("Upload CSV (World Stock Prices) — if none, sample data used", type=["csv","zip"])
use_sample = st.sidebar.checkbox("Use sample data (ignore upload)", False)

if uploaded and not use_sample:
    try:
        df = pd.read_csv(uploaded)
    except Exception:
        # try reading excel-like (pandas supports xls too), but for now show error
        st.sidebar.error("Couldn't read file as CSV. Ensure it's a valid CSV.")
        st.stop()
else:
    df = generate_sample_data()

# normalize columns and parse dates
df = try_parse_dates(df)

# check for required columns and give helpful guidance
required_cols = {"Date","Close","Brand_Name","Ticker"}
missing = [c for c in required_cols if c not in df.columns]
if missing:
    st.warning(f"Uploaded file missing columns: {missing}. Using sample data for visualization. You can map columns manually.")
    df = generate_sample_data()

# Ensure Date is datetime
df['Date'] = pd.to_datetime(df['Date'])
df['Year'] = df['Date'].dt.year
df['Month'] = df['Date'].dt.month
df['Month_str'] = df['Date'].dt.strftime("%Y-%m")
df['Day'] = df['Date'].dt.day

# Sidebar filters
min_date, max_date = df['Date'].min(), df['Date'].max()
st.sidebar.markdown(f"**Available date range:** {min_date.date()} — {max_date.date()}")

# Month selector: show month options present in data
month_options = sorted(df['Month_str'].unique(), reverse=True)
selected_month = st.sidebar.selectbox("Select month (for monthly / top/bottom)", month_options, index=0)

# Industry filter
industry_options = ["All"] + sorted(df['Industry_Tag'].dropna().unique().tolist())
selected_industry = st.sidebar.selectbox("Industry", industry_options, index=0)

# Number of top companies to show
top_k = st.sidebar.slider("Top / Bottom K (companies)", min_value=5, max_value=20, value=10)

# Animated selection: top N companies to animate
anim_n = st.sidebar.slider("Animate top N companies (animated chart)", min_value=2, max_value=10, value=5)

# -----------------------
# Data filtering
# -----------------------
month_df = df[df['Month_str'] == selected_month].copy()
if selected_industry != "All":
    month_df = month_df[month_df['Industry_Tag'] == selected_industry]

# Guard empty
if month_df.empty:
    st.error("No data for selected month/filters. Try different month or remove industry filter.")
    st.stop()

# compute averages per company for the selected month
company_avg = month_df.groupby(['Brand_Name','Ticker','Industry_Tag','Country']).agg(
    avg_close=('Close','mean'),
    lat=('lat','first'),
    lon=('lon','first')
).reset_index()

company_avg_sorted = company_avg.sort_values(by='avg_close', ascending=False)

top_companies = company_avg_sorted.head(top_k)
bottom_companies = company_avg_sorted.tail(top_k).sort_values(by='avg_close', ascending=True)

# -----------------------
# Layout (main)
# -----------------------
st.title("📈 Global Stock Market Dashboard (Streamlit)")
st.markdown(f"**Selected month:** `{selected_month}` • **Industry:** `{selected_industry}`")

# Summary metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Companies (month)", value=int(company_avg['Brand_Name'].nunique()))
with col2:
    st.metric("Avg Close (month)", f"${month_df['Close'].mean():.2f}")
with col3:
    st.metric("Total Volume (month)", f"{int(month_df['Volume'].sum()):,}")
with col4:
    # simple trend: lastDay vs firstDay for overall
    grouped_by_day = month_df.sort_values("Date").groupby("Date").agg(overall_close=('Close','mean')).reset_index()
    if len(grouped_by_day) >= 2:
        trend_pct = (grouped_by_day['overall_close'].iloc[-1] - grouped_by_day['overall_close'].iloc[0]) / grouped_by_day['overall_close'].iloc[0] * 100
        st.metric("Market Trend (month)", f"{trend_pct:+.2f}%")
    else:
        st.metric("Market Trend (month)", "N/A")

# -----------------------
# Charts Row 1: Monthly bar + Top10 pie + Bottom10 pie
# -----------------------
c1, c2, c3 = st.columns([1.4, 1, 1])

with c1:
    st.subheader("📊 Monthly Price Variation (average daily close)")
    # average close per day
    daily = month_df.groupby(month_df['Date'].dt.day).agg(avg_close=('Close','mean')).reset_index()
    daily = daily.sort_values(by='Date')
    fig_bar = px.bar(daily, x='Date', y='avg_close', labels={'Date':'Day of month','avg_close':'Average Close ($)'},
                     title=f"Daily average close — {selected_month}")
    fig_bar.update_layout(margin=dict(t=40, b=20))
    st.plotly_chart(fig_bar, use_container_width=True)

with c2:
    st.subheader(f"🏆 Top {top_k} Companies (current month avg)")
    fig_top = px.pie(top_companies, values='avg_close', names='Brand_Name',
                     title="Top companies by avg close (selected month)", hole=0.35)
    fig_top.update_traces(textinfo='percent+label')
    st.plotly_chart(fig_top, use_container_width=True)

with c3:
    st.subheader(f"📉 Bottom {top_k} Companies (current month avg)")
    fig_bot = px.pie(bottom_companies, values='avg_close', names='Brand_Name',
                     title="Bottom companies by avg close (selected month)", hole=0.35)
    fig_bot.update_traces(textinfo='percent+label')
    st.plotly_chart(fig_bot, use_container_width=True)

# -----------------------
# Map: Top 10 companies locations
# -----------------------
st.subheader("🌐 Top companies locations (map)")
map_col1, map_col2 = st.columns([2,1])
with map_col1:
    # center map around average lat lon
    top_map = top_companies.head(10).copy()
    avg_lat = top_map['lat'].mean() if not top_map['lat'].isna().all() else 0
    avg_lon = top_map['lon'].mean() if not top_map['lon'].isna().all() else 0
    m = folium.Map(location=[avg_lat, avg_lon], tiles="OpenStreetMap", zoom_start=2)
    for idx, r in top_map.iterrows():
        folium.CircleMarker(
            location=[r['lat'], r['lon']],
            radius=8,
            color=None,
            fill=True,
            fill_opacity=0.8,
            popup=(f"<b>{r['Brand_Name']}</b><br>Ticker: {r['Ticker']}<br>Avg: ${r['avg_close']:.2f}")
        ).add_to(m)
    st_folium(m, width="100%", height=450)

with map_col2:
    st.markdown("**Top companies (table)**")
    st.dataframe(top_map[['Brand_Name','Ticker','Industry_Tag','Country','avg_close']].rename(columns={'avg_close':'Avg Close ($)'}))

# -----------------------
# Animated chart: fluctuations of top N companies across the month
# -----------------------
st.subheader("📈 Animated stock price fluctuations (Top companies)")
# pick top N companies in the month by avg close
anim_companies = company_avg_sorted.head(anim_n)['Brand_Name'].tolist()
anim_df = month_df[month_df['Brand_Name'].isin(anim_companies)].copy()

# Plotly animated line chart: animation_frame by Date (string)
# to reduce frames, aggregate by day
anim_df['Date_str'] = anim_df['Date'].dt.strftime('%Y-%m-%d')
agg_anim = anim_df.groupby(['Date_str','Brand_Name']).agg(avg_close=('Close','mean')).reset_index()

fig_anim = px.line(agg_anim,
                   x='Date_str', y='avg_close', color='Brand_Name',
                   labels={'Date_str':'Date','avg_close':'Avg Close ($)'},
                   title=f"Daily close for top {anim_n} companies — animation-ready")
# Plotly doesn't auto-animate a normal line; use frames approach with px.line + animation_frame.
# Build animated scatter+lines using px.line with animation_frame
fig_frames = px.line(agg_anim, x='Date_str', y='avg_close', color='Brand_Name',
                     animation_frame='Date_str',
                     range_y=[agg_anim['avg_close'].min()*0.95, agg_anim['avg_close'].max()*1.05],
                     labels={'Date_str':'Date','avg_close':'Avg Close ($)'},
                     title=f"Animated daily close — Top {anim_n} companies")
fig_frames.update_layout(transition={'duration': 200}, showlegend=True, margin=dict(t=40))
# Show smaller friendly x axis labels
fig_frames.update_xaxes(tickangle= -45, tickmode='auto', nticks=8)
st.plotly_chart(fig_frames, use_container_width=True, config={'displayModeBar': True})

# -----------------------
# Data explorer & download
# -----------------------
st.markdown("---")
st.subheader("🔎 Data explorer")
explore_col1, explore_col2 = st.columns([3,1])
with explore_col1:
    st.write("Filtered (month + industry) sample rows:")
    st.dataframe(month_df.sample(min(200, len(month_df))))
with explore_col2:
    st.markdown("Download filtered data:")
    csv = month_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download CSV (filtered)", data=csv, file_name=f"stock_filtered_{selected_month}.csv", mime="text/csv")

st.caption("App generated by Streamlit — you can upload your full 'World Stock Prices' CSV with columns like Date, Open, High, Low, Close, Volume, Brand_Name, Ticker, Industry_Tag, Country, lat, lon. If lat/lon missing, map markers won't show.")

# -----------------------
# Footer / tips
# -----------------------
st.markdown("---")
st.write("Tips: If your CSV uses different column names, rename them before upload or modify the script to map your names to expected ones (Date, Close, Brand_Name, Ticker, Industry_Tag, lat, lon).")
