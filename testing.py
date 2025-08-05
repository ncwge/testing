import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="AJMadison SKU Lookup", layout="centered")
st.title("AJMadison SKU Lookup")

API_URL = "https://ajmadison-scraper-api.onrender.com/scrape"

sku = st.text_input("Enter SKU (model number)", placeholder="e.g. SHV9PCM3N").strip().upper()

if st.button("Fetch") and sku:
    st.info(f"Fetching data for SKU: {sku}")
    try:
        response = requests.post(API_URL, json={"sku": sku}, timeout=20)
        response.raise_for_status()
        data = response.json()
        if not data or len(data) <= 1:
            st.warning("No specs found for that SKU.")
        else:
            st.subheader(f"Extracted Specs for {sku}")
            rows = [{"Attribute": k.replace('_', ' ').capitalize(), "Value": v}
                    for k, v in data.items() if k != "sku"]
            df = pd.DataFrame(rows)
            st.table(df)
    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
