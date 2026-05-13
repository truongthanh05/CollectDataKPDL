import streamlit as st
import pandas as pd

st.title("Phân tích hành vi khách hàng du lịch")

df = pd.read_csv(
    "data/processed/cleaned_hotels.csv"
)

st.subheader("Dữ liệu khách sạn")

st.dataframe(df)

st.subheader("Chọn dịch vụ")

hotel_type = st.selectbox(
    "Loại khách sạn",
    df["hotel_type"].unique()
)

meal_plan = st.selectbox(
    "Gói ăn",
    df["meal_plan"].unique()
)

st.subheader("Gợi ý combo")

if hotel_type == "Hotel" and meal_plan == "Breakfast":

    st.success("""
    Gợi ý:
    - Swimming
    - Beach
    - Family Trip
    """)