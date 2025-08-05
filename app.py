import re
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
from io import BytesIO

st.set_page_config(page_title="Multi-Site Appliance SKU Scraper", layout="centered")
st.title("Multi-Site Appliance SKU Scraper")

# --- Site-specific scraping attempts using search engines ---
def try_search_engine(sku):
    """Use Bing Search API to find a trusted retailer page."""
    import os
    import urllib.parse
    BING_API_KEY = os.getenv("BING_API_KEY")
    if not BING_API_KEY:
        return None

    trusted_sites = [
        "plessers.com", "us-appliance.com", "brothersmain.com",
        "designerappliances.com", "fergusonhome.com", "groveappliance.com"
    ]

    query = f"{sku} dimensions and features " + " OR ".join([f"site:{site}" for site in trusted_sites])
    encoded_query = urllib.parse.quote(query)
    search_url = f"https://api.bing.microsoft.com/v7.0/search?q={encoded_query}"

    headers = {"Ocp-Apim-Subscription-Key": BING_API_KEY}

    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        for item in data.get("webPages", {}).get("value", []):
            url = item.get("url", "")
            if any(site in url for site in trusted_sites):
                # Fetch and scrape the first trusted page
                product_resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                soup = BeautifulSoup(product_resp.text, "html.parser")

                # Generic spec extraction
                data_dict = {}
                for row in soup.select("table tr"):
                    cells = row.find_all(["td", "th"])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True).lower().replace(" ", "_")
                        val = cells[1].get_text(strip=True)
                        if key and val:
                            data_dict[key] = val

                if data_dict:
                    return data_dict
        return None

    except Exception as e:
        print(f"Search error for {sku}: {e}")
        return None

# Define scraping order with Bing-based discovery first
fallback_sites = [try_search_engine]

# --- Primary scraper logic ---
def scrape_product_data(sku):
    result = {"sku": sku, "status": "Not found", "source": None, "data": {}}

    for fallback in fallback_sites:
        specs = fallback(sku)
        if specs:
            result.update({"status": "OK", "source": fallback.__name__.replace("try_", ""), "data": specs})
            return result

    return result

# --- Streamlit UI ---
st.markdown("Upload an Excel or text file with one column of SKUs, or paste below. Results returned as JSON. Requires BING_API_KEY in environment.")

uploaded_file = st.file_uploader("Upload Excel (.xlsx) or Text (.txt) file", type=["xlsx", "txt"])
manual_input = st.text_area("Or paste SKUs here (one per line)", height=150)

if uploaded_file or manual_input:
    try:
        if uploaded_file:
            if uploaded_file.name.endswith(".xlsx"):
                df_input = pd.read_excel(uploaded_file)
                if df_input.empty or df_input.shape[1] != 1:
                    st.error("Please upload a file with exactly one column of SKUs.")
                    st.stop()
                skus = df_input.iloc[:, 0].dropna().astype(str).str.upper().tolist()

            elif uploaded_file.name.endswith(".txt"):
                content = uploaded_file.read().decode("utf-8")
                skus = [line.strip().upper() for line in content.splitlines() if line.strip()]

            else:
                st.error("Unsupported file type. Upload .xlsx or .txt")
                st.stop()

        else:
            skus = [line.strip().upper() for line in manual_input.splitlines() if line.strip()]

        if st.button("Start Scraping"):
            results = []
            for idx, sku in enumerate(skus):
                st.info(f"Processing {sku} ({idx + 1}/{len(skus)})...")
                product_data = scrape_product_data(sku)
                results.append(product_data)
                time.sleep(2)  # gentle pacing

            st.success("Scraping complete!")
            st.json(results)

            json_str = json.dumps(results, indent=2)
            st.download_button("Download JSON", data=json_str, file_name="appliance_specs.json", mime="application/json")

    except Exception as e:
        st.error(f"Failed to process input: {e}")
