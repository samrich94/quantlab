import streamlit as st
import boto3
import json
import pandas as pd
import plotly.express as px
import logging
from scipy.stats import zscore

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS S3 Configuration
BUCKET = 'quantlab-bucket'
BREADTH_FILE = 'breadth_data.json'

# Initialize S3 client
try:
    s3 = boto3.client('s3', region_name='eu-west-2')
except Exception as e:
    st.error(f"Failed to initialize S3 client: {e}")
    st.stop()

# Function to fetch data from S3
@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_breadth_data():
    try:
        response = s3.get_object(Bucket=BUCKET, Key=BREADTH_FILE)
        breadth_data = json.loads(response['Body'].read().decode('utf-8'))
        return breadth_data
    except Exception as e:
        logger.error(f"Error fetching breadth data from S3: {e}")
        return None

# Streamlit App
st.set_page_config(page_title="QuantLab Dashboard", layout="wide")
st.title("QuantLab Dashboard")

# Fetch data
breadth_data = fetch_breadth_data()
if not breadth_data:
    st.error("Failed to load data from S3. Please check the Lambda function and S3 bucket.")
    st.stop()

# Display timestamp
st.markdown(f"**Data last updated:** {breadth_data['timestamp']}")

# Organize data for display
data = breadth_data['data']
vol_data = data['Volatility']

# Create a DataFrame for the main table
table_data = []
for index, metrics in data.items():
    if index not in ['SPY_Flow', 'Currencies', 'Volatility']:
        row = {'Index': index}
        row.update({
            'Momentum Factor': metrics.get('momentum_factor', 'N/A'),
            '% 52W High': metrics.get('percent_52w_high', 'N/A')
        })
        table_data.append(row)

df = pd.DataFrame(table_data)

# Display the main table
st.subheader("Breadth and Momentum Data")
st.dataframe(df, use_container_width=True)

# Display SPY Options Data
st.subheader("SPY Options Data")
options_data = data['SPY_Options']
st.markdown(
    f"- **Put/Call Ratio:** {options_data.get('put_call_ratio', 'N/A'):.2f}\n"
    f"- **Open Interest:** {options_data.get('open_interest', 'N/A'):,}\n"
    f"- **Implied Volatility:** {options_data.get('implied_volatility', 'N/A'):.2f}"
)

# Display SPY Order Flow
st.subheader("SPY Order Flow")
flow = data.get('SPY_Flow', {})
if flow:
    st.markdown(
        f"- **Put Buys:** {flow.get('put_buys', 0):,}\n"
        f"- **Put Sells:** {flow.get('put_sells', 0):,}\n"
        f"- **Call Buys:** {flow.get('call_buys', 0):,}\n"
        f"- **Call Sells:** {flow.get('call_sells', 0):,}\n"
        f"- **Whale Sentiment:** {flow.get('whale_sentiment', 'N/A')}"
    )

# Display Volatility Data
st.subheader("Volatility Metrics")
st.markdown(
    f"- **VIX Term Structure:** {vol_data.get('vix_term_structure', 'N/A'):.2f}\n"
    f"- **VIX Z-Score:** {vol_data.get('z_score_vix', 'N/A'):.2f}\n"
    f"- **VIX Volatility Clustering:** {vol_data.get('vol_clustering_vix', 'N/A'):.4f}"
)
if vol_data.get('vix_term_structure', 0) > 0.05:
    st.warning("Market in Backwardation (Potential Bearish Signal)")

# Display Currency Data
st.subheader("Currency Metrics")
curr_data = data['Currencies']
st.markdown(
    f"- **EUR/USD:** {curr_data.get('eur_usd', 'N/A'):.4f}\n"
    f"- **GBP/USD:** {curr_data.get('gbp_usd', 'N/A'):.4f}\n"
    f"- **EUR/USD Z-Score:** {curr_data.get('z_score_eur_usd', 'N/A'):.2f}\n"
    f"- **GBP/USD Z-Score:** {curr_data.get('z_score_gbp_usd', 'N/A'):.2f}\n"
    f"- **EUR/USD Volatility Clustering:** {curr_data.get('vol_clustering_eur_usd', 'N/A'):.4f}\n"
    f"- **GBP/USD Volatility Clustering:** {curr_data.get('vol_clustering_gbp_usd', 'N/A'):.4f}"
)

# Optional: Add charts for key metrics
st.subheader("Visualizations")
if not fmp_stock_data.empty:
    st.line_chart(fmp_stock_data['close'].tail(30), use_container_width=True)

# Footer
st.markdown("---")
st.markdown("Built with Streamlit | Data sourced from FMP and Polygon.io")