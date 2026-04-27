from datetime import datetime
import random
from zoneinfo import ZoneInfo

import streamlit as st
import requests

from backend import running_backend

st.set_page_config(
    page_title="Database Automated Update/Checker",
    page_icon="📂",
    layout="centered"
)

st.title("Get Database Update/Checker")

# ---- TEXT INPUT SECTION ----
st.subheader("Order Numbers below (one per line)")
text1 = st.text_area("Enter order numbers (one per line)", height=100)

if st.button("Submit Text Data"):
    order_numbers = [order.strip() for order in text1.split("\n") if order.strip()]

    print("Order numbers submitted:", order_numbers)

    # res = requests.post(
    #     "http://127.0.0.1:8000/submit_data",
    #     json=payload
    # )

    running_backend()  # Call the backend processing function

    st.download_button(
        label="Download Processed CSV",
        data=open("extracted_orders.csv", "rb").read(),
        file_name="extracted_orders.csv",
        mime="text/csv"
    )