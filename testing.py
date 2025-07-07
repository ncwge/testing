import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.title("Competitor SKU Extractor")

st.header("Step 1: Enter Competitor SKUs")
uploaded_file = st.file_uploader("Upload Excel file with SKUs", type=["xlsx", "xls"])
pasted_data = st.text_area("Paste competitor SKU data here:")

def extract_skus_from_excel(df):
    all_text = df.astype(str).values.flatten()
    sku_pattern = re.compile(r"\b[A-Z]{2,}[0-9]{2,}[A-Z0-9]*\b")
    skus = []
    seen = set()
    for text in all_text:
        matches = sku_pattern.findall(text)
        for match in matches:
            if len(match) >= 6 and match not in seen:
                skus.append(match)
                seen.add(match)
    return skus

def extract_skus_from_text(text):
    sku_pattern = re.compile(r"\b[A-Z]{2,}[0-9]{2,}[A-Z0-9]*\b")
    skus = []
    seen = set()
    for line in text.upper().splitlines():
        matches = sku_pattern.findall(line)
        for sku in matches:
            if len(sku) >= 6 and sku not in seen:
                skus.append(sku)
                seen.add(sku)
    return skus

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# Determine source of SKU input
skus = []
if uploaded_file:
    df_upload = pd.read_excel(uploaded_file, header=None)
    skus = extract_skus_from_excel(df_upload)
elif pasted_data.strip():
    skus = extract_skus_from_text(pasted_data)

# Output results
if skus:
    st.success(f"✅ Found {len(skus)} unique SKUs:")
    sku_df = pd.DataFrame({'SKU': skus})
    st.dataframe(sku_df)
    excel_data = to_excel(sku_df)
    st.download_button(
        "Download SKUs to Excel",
        data=excel_data,
        file_name="sku_output.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Please upload a file or paste SKU data above.")
