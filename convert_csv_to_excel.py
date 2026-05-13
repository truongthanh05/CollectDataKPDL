import pandas as pd

# =========================
# ĐỌC FILE CSV
# =========================

df = pd.read_csv(
    "traveloka_hotels_full.csv"
)

# =========================
# TÁCH nearby_places
# =========================

max_places = 10

for i in range(max_places):

    df[f"place_{i+1}"] = (
        df["nearby_places"]
        .fillna("")
        .apply(
            lambda x:
            x.split(" | ")[i]
            if len(x.split(" | ")) > i
            else ""
        )
    )

# =========================
# XÓA CỘT GỘP
# =========================

df = df.drop(columns=["nearby_places"])

# =========================
# LƯU EXCEL
# =========================

df.to_excel(
    "traveloka_hotels_full.xlsx",
    index=False
)

print("Đã tạo file Excel")