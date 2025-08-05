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

# --- Site-specific scraping attempts ---
def try_us_appliance(sku):
    url = f"https://www.us-appliance.com/{sku}.html"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        data = {}
        for tr in soup.select("table tr"):
            tds = tr.find_all("td")
            if len(tds) == 2:
                key = tds[0].get_text(strip=True).lower().replace(" ", "_")
                val = tds[1].get_text(strip=True)
                data[key] = val
        return data if data else None
    except:
        return None

def try_brothersmain(sku):
    url = f"https://www.brothersmain.com/products/{sku}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        data = {}
        for row in soup.select(".product-specs-table tr"):
            cells = row.find_all("td")
            if len(cells) == 2:
                key = cells[0].get_text(strip=True).lower().replace(" ", "_")
                val = cells[1].get_text(strip=True)
                data[key] = val
        return data if data else None
    except:
        return None

def try_plessers(sku):
    search_url = f"https://www.plessers.com/search_results.php?search_query={sku}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        search_resp = requests.get(search_url, headers=headers, timeout=10)
        search_soup = BeautifulSoup(search_resp.text, "html.parser")
        link = search_soup.select_one(".product-listing a")
        if not link:
            return None
        product_url = "https://www.plessers.com" + link["href"]
        product_resp = requests.get(product_url, headers=headers, timeout=10)
        soup = BeautifulSoup(product_resp.text, "html.parser")
        data = {}
        for tr in soup.select(".specs tr"):
            tds = tr.find_all("td")
            if len(tds) == 2:
                key = tds[0].get_text(strip=True).lower().replace(" ", "_")
                val = tds[1].get_text(strip=True)
                data[key] = val
        return data if data else None
    except:
        return None

# Define scraping order excluding AJMadison
fallback_sites = [try_us_appliance, try_brothersmain, try_plessers]

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
st.markdown("Upload an Excel or text file with one column of SKUs. Scraped results will be returned as JSON.")

uploaded_file = st.file_uploader("Upload Excel (.xlsx) or Text (.txt) file", type=["xlsx", "txt"])

if uploaded_file:
    try:
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

        if st.button("Start Scraping"):
            results = []
            for idx, sku in enumerate(skus):
                st.info(f"Processing {sku} ({idx + 1}/{len(skus)})...")
                product_data = scrape_product_data(sku)
                results.append(product_data)
                time.sleep(3)  # gentle pacing

            st.success("Scraping complete!")
            st.json(results)

            json_str = json.dumps(results, indent=2)
            st.download_button("Download JSON", data=json_str, file_name="appliance_specs.json", mime="application/json")

    except Exception as e:
        st.error(f"Failed to process file: {e}")
