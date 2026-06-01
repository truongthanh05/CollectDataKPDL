import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]

DATA_FILE = ROOT_DIR / "data" / "processed" / "traveloka_hotels_cleaned.xlsx"
OUTPUT_DIR = ROOT_DIR / "data" / "output"

REGIONS = [
    "Hồ Chí Minh",
    "Hà Nội",
    "Vũng Tàu",
    "Phan Thiết",
    "Mũi Né",
    "Đà Lạt",
    "Huế",
    "Đà Nẵng",
    "Nha Trang",
    "Phú Quốc",
]


REGION_IMAGE_MAP = {
    "Hồ Chí Minh": "ho_chi_minh.jpg",
    "Hà Nội": "ha_noi.jpg",
    "Vũng Tàu": "vung_tau.jpg",
    "Phan Thiết": "phan_thiet.jpg",
    "Mũi Né": "mui_ne.jpg",
    "Đà Lạt": "da_lat.jpg",
    "Huế": "hue.jpg",
    "Đà Nẵng": "da_nang.jpg",
    "Nha Trang": "nha_trang.jpg",
    "Phú Quốc": "phu_quoc.jpg",
}


REGION_ALIASES = {
    "tp hồ chí minh": "Hồ Chí Minh",
    "tp. hồ chí minh": "Hồ Chí Minh",
    "thành phố hồ chí minh": "Hồ Chí Minh",
    "hồ chí minh": "Hồ Chí Minh",
    "ho chi minh": "Hồ Chí Minh",
    "sài gòn": "Hồ Chí Minh",
    "sai gon": "Hồ Chí Minh",

    "hà nội": "Hà Nội",
    "ha noi": "Hà Nội",

    "vũng tàu": "Vũng Tàu",
    "vung tau": "Vũng Tàu",

    "phan thiết": "Phan Thiết",
    "phan thiet": "Phan Thiết",

    "mũi né": "Mũi Né",
    "mui ne": "Mũi Né",

    "đà lạt": "Đà Lạt",
    "đà lạt ": "Đà Lạt",
    "da lat": "Đà Lạt",
    "đà lạt": "Đà Lạt",
    "đà lạt.": "Đà Lạt",

    "huế": "Huế",
    "hue": "Huế",

    "đà nẵng": "Đà Nẵng",
    "da nang": "Đà Nẵng",

    "nha trang": "Nha Trang",

    "phú quốc": "Phú Quốc",
    "phu quoc": "Phú Quốc",
}


def normalize_space(text):
    if pd.isna(text):
        return ""
    text = str(text).strip()
    text = re.sub(r"\s+", " ", text)
    return text


def remove_accents(text):
    text = str(text)
    text = unicodedata.normalize("NFD", text)
    text = "".join(
        ch for ch in text
        if unicodedata.category(ch) != "Mn"
    )
    text = text.replace("đ", "d").replace("Đ", "D")
    return text


def text_key(text):
    return remove_accents(normalize_space(text).lower())


def normalize_region(value):
    raw = normalize_space(value)
    key = raw.lower()
    key_no_acc = text_key(raw)

    # Match exact with accents
    if key in REGION_ALIASES:
        return REGION_ALIASES[key]

    # Match without accents
    for alias, region in REGION_ALIASES.items():
        if text_key(alias) == key_no_acc:
            return region

    # Fuzzy contains
    for alias, region in REGION_ALIASES.items():
        if text_key(alias) in key_no_acc:
            return region

    return raw


def split_items(value):
    """
    Tách chuỗi dạng A | B | C thành list.
    """
    if pd.isna(value):
        return []
    text = str(value).replace("\n", " | ")
    parts = re.split(r"\s*\|\s*", text)
    return [
        normalize_space(part)
        for part in parts
        if normalize_space(part)
    ]


def make_item(prefix, value):
    value = normalize_space(value).lower()
    value = remove_accents(value)
    value = re.sub(r"[^a-zA-Z0-9]+", "_", value)
    value = value.strip("_")
    if not value:
        return ""
    return f"{prefix}_{value}"


def clean_float(value):
    if pd.isna(value):
        return np.nan
    text = str(value).replace(",", ".")
    match = re.search(r"\d+(\.\d+)?", text)
    if not match:
        return np.nan
    return float(match.group())


def clean_int(value):
    if pd.isna(value):
        return np.nan
    text = str(value)
    match = re.search(r"\d+", text)
    if not match:
        return np.nan
    return int(match.group())


def clean_price(value):
    if pd.isna(value):
        return np.nan
    text = str(value)
    digits = re.sub(r"[^\d]", "", text)
    if not digits:
        return np.nan
    return int(digits)


def ensure_numeric_columns(df):
    df = df.copy()

    if "price_clean" not in df.columns and "price" in df.columns:
        df["price_clean"] = df["price"].apply(clean_price)

    if "overall_rating_clean" not in df.columns and "overall_rating" in df.columns:
        df["overall_rating_clean"] = df["overall_rating"].apply(clean_float)

    if "star_rating_clean" not in df.columns and "star_rating" in df.columns:
        df["star_rating_clean"] = df["star_rating"].apply(clean_float)

    if "review_count_clean" not in df.columns and "review_count" in df.columns:
        df["review_count_clean"] = df["review_count"].apply(clean_int)

    if "price_level" not in df.columns and "price_clean" in df.columns:
        df["price_level"] = df["price_clean"].apply(price_level)

    if "rating_level" not in df.columns and "overall_rating_clean" in df.columns:
        df["rating_level"] = df["overall_rating_clean"].apply(rating_level)

    return df


def price_level(price):
    if pd.isna(price):
        return ""
    if price < 500000:
        return "Giá rẻ"
    if price < 1000000:
        return "Giá trung bình"
    return "Giá cao"


def rating_level(rating):
    if pd.isna(rating):
        return ""
    if rating >= 9:
        return "Rating xuất sắc"
    if rating >= 8:
        return "Rating cao"
    if rating >= 7:
        return "Rating khá"
    return "Rating thấp"


def load_hotels(path=DATA_FILE):
    if not Path(path).exists():
        raise FileNotFoundError(
            f"Không tìm thấy file dữ liệu: {path}. "
            "Hãy đặt file traveloka_hotels_cleaned.xlsx vào data/processed/"
        )

    df = pd.read_excel(path)
    df.columns = [normalize_space(c) for c in df.columns]

    # Xóa cột Excel rác
    unnamed_cols = [
        c for c in df.columns
        if str(c).startswith("Unnamed")
    ]
    df = df.drop(columns=unnamed_cols, errors="ignore")
    df = df.dropna(axis=1, how="all")

    if "region" in df.columns:
        df["region"] = df["region"].apply(normalize_region)

    df = ensure_numeric_columns(df)

    # Chuẩn hóa các cột text cần có
    for col in [
        "hotel_name",
        "hotel_url",
        "address",
        "district",
        "nearby_places",
        "nearby_places_clean",
        "tourism_tags",
        "facilities_clean",
        "price_level",
        "rating_level",
    ]:
        if col not in df.columns:
            df[col] = ""

    # Ưu tiên nearby_places_clean, nếu trống thì dùng nearby_places
    df["nearby_text_for_app"] = df["nearby_places_clean"]
    mask_empty_nearby = df["nearby_text_for_app"].astype(str).str.strip().eq("")
    df.loc[mask_empty_nearby, "nearby_text_for_app"] = df.loc[mask_empty_nearby, "nearby_places"]

    return df


PLACE_TYPE_RULES = {
    "vui_choi_giai_tri": [
        "pho di bo", "ho xuan huong", "cong vien", "quang truong",
        "cho dem", "nha hat", "san van dong", "bui vien",
        "nguyen hue", "mega gs", "cinema", "rap", "cloud9", "bar"
    ],
    "shopping_an_uong": [
        "cho", "market", "mall", "plaza", "vincom", "takashimaya",
        "saigon centre", "lotte", "coopmart", "big c", "go!",
        "cua hang", "sieu thi", "dong ba", "ben thanh", "da lat"
    ],
    "van_hoa_di_tich": [
        "dai noi", "kinh thanh", "lang", "chua", "nha tho",
        "bao tang", "dinh", "pho co", "cau truong tien", "song huong",
        "doc lap", "duc ba", "thap"
    ],
    "bien_nghi_duong": [
        "bien", "beach", "mui ne", "hon rom", "bai sau",
        "bai truoc", "bai dai", "dao", "vinwonders", "hon chong",
        "hon mun"
    ],
    "san_bay_cong_tac": [
        "san bay", "airport", "tan son nhat", "noi bai",
        "phu bai", "cam ranh", "lien khuong"
    ],
    "y_te": [
        "benh vien", "hospital", "phong kham", "y khoa", "tam anh",
        "cho ray"
    ],
    "giao_thong": [
        "ga ", "ga metro", "ben xe", "station", "cang", "port", "bus"
    ],
}


PURPOSE_LABELS = {
    "vui_choi_giai_tri": "Vui chơi / giải trí",
    "shopping_an_uong": "Mua sắm / ăn uống",
    "van_hoa_di_tich": "Tham quan văn hóa / di tích",
    "bien_nghi_duong": "Du lịch biển / nghỉ dưỡng",
    "san_bay_cong_tac": "Công tác / transit sân bay",
    "y_te": "Lưu trú y tế",
    "giao_thong": "Gần điểm giao thông",
}


PURPOSE_TO_SERVICES = {
    "Vui chơi / giải trí": [
        "Lịch trình buổi tối",
        "Gợi ý điểm check-in gần khách sạn",
        "Taxi/Grab đi chơi",
        "Gửi hành lý",
        "Check-out muộn",
    ],
    "Mua sắm / ăn uống": [
        "Food tour",
        "Gợi ý quán ăn gần khách sạn",
        "Taxi nội thành",
        "Lịch trình mua sắm",
    ],
    "Tham quan văn hóa / di tích": [
        "City tour",
        "Thuê hướng dẫn viên",
        "Thuê xe tham quan",
        "Gợi ý lịch trình văn hóa",
    ],
    "Du lịch biển / nghỉ dưỡng": [
        "Tour biển",
        "Thuê xe máy",
        "Gợi ý hải sản",
        "Spa / hồ bơi",
    ],
    "Công tác / transit sân bay": [
        "Đưa đón sân bay",
        "Check-in nhanh",
        "Gửi hành lý",
        "Taxi/Grab sân bay",
        "Giặt ủi",
    ],
    "Lưu trú y tế": [
        "Phòng yên tĩnh",
        "Dịch vụ giặt ủi",
        "Thang máy",
        "Cửa hàng tiện lợi gần khách sạn",
    ],
    "Gần điểm giao thông": [
        "Taxi/Grab",
        "Gửi hành lý",
        "Check-in nhanh",
    ],
}


def classify_place_types(nearby_text):
    text = text_key(nearby_text)
    matched = []

    for place_type, keywords in PLACE_TYPE_RULES.items():
        for keyword in keywords:
            if text_key(keyword) in text:
                matched.append(place_type)
                break

    return matched


def infer_purposes_from_row(row):
    """
    Tận dụng tourism_tags có sẵn + nearby_places.
    """
    purposes = []

    tourism_tags = split_items(row.get("tourism_tags", ""))
    for tag in tourism_tags:
        tag_key = text_key(tag)
        for label in PURPOSE_LABELS.values():
            if text_key(label) in tag_key or any(word in tag_key for word in text_key(label).split("_")):
                purposes.append(label)

        # Mapping mềm theo text
        if "mua sam" in tag_key or "an uong" in tag_key:
            purposes.append("Mua sắm / ăn uống")
        if "tham quan" in tag_key or "van hoa" in tag_key or "di tich" in tag_key:
            purposes.append("Tham quan văn hóa / di tích")
        if "bien" in tag_key or "nghi duong" in tag_key:
            purposes.append("Du lịch biển / nghỉ dưỡng")
        if "san bay" in tag_key or "transit" in tag_key or "cong tac" in tag_key:
            purposes.append("Công tác / transit sân bay")
        if "y te" in tag_key:
            purposes.append("Lưu trú y tế")
        if "vui choi" in tag_key or "giai tri" in tag_key:
            purposes.append("Vui chơi / giải trí")

    place_types = classify_place_types(row.get("nearby_text_for_app", ""))
    for pt in place_types:
        label = PURPOSE_LABELS.get(pt)
        if label:
            purposes.append(label)

    return list(dict.fromkeys([p for p in purposes if p]))


def get_all_facilities(df):
    items = set()
    for value in df.get("facilities_clean", pd.Series(dtype=str)).fillna(""):
        for item in split_items(value):
            items.add(item)
    return sorted(items)


def get_all_purposes(df):
    purposes = set()
    for _, row in df.iterrows():
        for p in infer_purposes_from_row(row):
            purposes.add(p)
    return sorted(purposes)


def service_suggestions_for_purpose(purpose):
    return PURPOSE_TO_SERVICES.get(purpose, [])


def format_vnd(value):
    if pd.isna(value):
        return "N/A"
    try:
        return f"{int(value):,} VND".replace(",", ".")
    except Exception:
        return str(value)
