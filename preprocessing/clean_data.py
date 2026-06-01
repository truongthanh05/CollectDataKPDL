import pandas as pd
import os


def clean_hotels_data():

    input_path = "../data/raw/raw_hotels.csv"

    df = pd.read_csv(input_path)

    # xóa dòng null
    df = df.dropna()

    # xóa trùng
    df = df.drop_duplicates()

    # chuẩn hóa text
    df["hotel_name"] = df["hotel_name"].str.strip()

    # reset index
    df = df.reset_index(drop=True)

    # tạo folder nếu chưa có
    os.makedirs("../data/processed", exist_ok=True)

    output_path = "../data/processed/cleaned_hotels.csv"

    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print("Đã làm sạch dữ liệu")


if __name__ == "__main__":
    clean_hotels_data()