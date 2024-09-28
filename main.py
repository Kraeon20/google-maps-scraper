import streamlit as st
from scrape import main
import pandas as pd
import io
import json

# st.markdown(
#     """
#     <style>
#     footer {visibility: hidden;}
#     header {visibility: hidden;}
#     </style>
#     """,
#     unsafe_allow_html=True
# )



st.title("GOOGLE MAPS SCRAPER")

col1, col2 = st.columns(2)

with col1:
    keyword = st.text_input("Enter your search term:")

with col2:
    total = st.text_input("Number of results to scrape:")

if total.isdigit():
    total = int(total)
else:
    total = 0

def convert_df_to_json(df):
    json_data = df.to_json(orient="records")
    formatted_json = json.dumps(json.loads(json_data), indent=4)
    return formatted_json

if st.button("Scrape Google Maps"):
    if keyword and total > 0:
        st.write(f"Scraping {total} results for '{keyword}'...")
        progress = st.progress(0)

        result_df, total_found = main(search_term=keyword, quantity=total, progress=progress)

        if isinstance(result_df, pd.DataFrame) and not result_df.empty:
            st.session_state.result_df = result_df
            st.session_state.total_found = total_found
        else:
            st.session_state.result_df = None
            st.session_state.total_found = None
            
    else:
        st.warning("Please enter a valid search term and number of results.")

if 'result_df' in st.session_state:
    result_df = st.session_state.result_df
    total_found = st.session_state.total_found

    if result_df is not None:
        result_df.index = result_df.index + 1
        st.success(f"Successfully scraped {len(result_df)} out of {total} results.")
        st.dataframe(result_df)

        csv_data = result_df.to_csv(index=False).encode('utf-8')
        excel_data = io.BytesIO()
        result_df.to_excel(excel_data, index=False, engine='openpyxl')
        json_data = convert_df_to_json(result_df)

        col1, col2 = st.columns(2)

        with col1:
            download_format = st.selectbox("Download data as:", ["CSV", "Excel", "JSON"], key="download_select", label_visibility="collapsed")

        with col2:
            if download_format == "CSV":
                st.download_button(
                    label="Download",
                    data=csv_data,
                    file_name='scraped_data.csv',
                    mime='text/csv',
                    key="csv_download"
                )
            elif download_format == "Excel":
                st.download_button(
                    label="Download",
                    data=excel_data.getvalue(),
                    file_name='scraped_data.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    key="excel_download"
                )
            elif download_format == "JSON":
                st.download_button(
                    label="Download",
                    data=json_data,
                    file_name='scraped_data.json',
                    mime='application/json',
                    key="json_download"
                )
    else:
        st.error("No results found.")