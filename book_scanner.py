import streamlit as st
import pandas as pd
import requests
import base64
from openai import OpenAI

# Page setup
st.set_page_config(page_title="eBay Book Valuer", layout="wide")

st.title("📚 Multi-Book Price & Velocity Scanner")
st.write("Upload a photo of your books to find their **eBay.ca** listed prices and sales frequency.")

# Sidebar for API Keys
with st.sidebar:
    st.header("🔑 API Configuration")
    os_key = st.text_input("OpenAI API Key", type="password")
    serp_key = st.text_input("SerpApi Key (for eBay)", type="password")
    st.markdown("[Get SerpApi Key](https://serpapi.com/) | [Get OpenAI Key](https://platform.openai.com/)")

# Helper: Identify Books from Image
def get_book_list(image_bytes):
    client = OpenAI(api_key=os_key)
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": [
            {"type": "text", "text": "List every book title and author in this image as a simple comma-separated list."},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        ]}]
    )
    return response.choices[0].message.content.split(',')

# Helper: Get eBay Prices
def fetch_ebay_data(query):
    url = "https://serpapi.com/search"
    params = {
        "engine": "ebay",
        "_nkw": query,
        "ebay_domain": "ebay.ca",
        "api_key": serp_key,
        "_lh_Sold": "1" 
    }
    r = requests.get(url, params=params).json()
    solds = r.get("sold_results", [])
    prices = sorted([s.get("price", {}).get("extracted", 0) for s in solds if s.get("price")])
    
    avg_low = sum(prices[:3]) / 3 if len(prices) >= 3 else 0
    return avg_low, len(solds)

# App UI Logic
up_file = st.file_uploader("Upload Image", type=['jpg', 'png', 'jpeg'])

if up_file and os_key and serp_key:
    if st.button("Analyze Books"):
        with st.spinner("Reading spines and checking eBay..."):
            titles = get_book_list(up_file.getvalue())
            data_rows = []
            
            for t in titles:
                price, volume = fetch_ebay_data(t.strip())
                data_rows.append({
                    "Book": t.strip(),
                    "Avg Low List (CAD)": f"${price:.2f}",
                    "Solds (90 Days)": volume,
                    "3-Year Trend": "🔥 High" if volume > 10 else "💎 Niche"
                })
            
            st.table(pd.DataFrame(data_rows))
else:
    st.info("Please upload an image and provide your API keys in the sidebar.")
