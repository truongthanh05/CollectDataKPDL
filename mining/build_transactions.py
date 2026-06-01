from pathlib import Path
import sys, re, unicodedata
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))
from recommender.utils import DATA_FILE, OUTPUT_DIR, load_hotels, split_items

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TRANSACTION_FILE = OUTPUT_DIR / "transactions.csv"
ONEHOT_FILE = OUTPUT_DIR / "onehot.csv"
ITEM_DICTIONARY_FILE = OUTPUT_DIR / "item_dictionary.csv"
ITEM_DICT = {}

def remove_accents(text):
    text = unicodedata.normalize("NFD", str(text))
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.replace("đ", "d").replace("Đ", "D")

def slug(text):
    text = remove_accents(str(text).lower().strip())
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")

def add_item(items, code, label, group):
    if code:
        items.append(code)
        ITEM_DICT.setdefault(code, {"item": code, "label": label, "group": group})

def contains_any(text, keywords):
    s = slug(text)
    return any(slug(k) in s for k in keywords)

PLACE_RULES = {
    "purpose_vui_choi_giai_tri": ("Mục đích: vui chơi / giải trí", ["phố đi bộ","bùi viện","nguyễn huệ","hồ xuân hương","công viên","quảng trường","chợ đêm","nhà hát","rạp","cinema"]),
    "purpose_mua_sam_an_uong": ("Mục đích: mua sắm / ăn uống", ["chợ","market","mall","plaza","vincom","lotte","takashimaya","saigon centre","siêu thị","food","restaurant"]),
    "purpose_tham_quan_van_hoa": ("Mục đích: tham quan văn hóa / di tích", ["đại nội","kinh thành","lăng","chùa","bảo tàng","nhà thờ","dinh","phố cổ","cầu trường tiền","sông hương","hoàn kiếm","ngọc sơn"]),
    "purpose_du_lich_bien_nghi_duong": ("Mục đích: du lịch biển / nghỉ dưỡng", ["biển","beach","mũi né","bãi sau","bãi trước","hòn rơm","bãi dài","đảo","vinwonders","hòn chồng"]),
    "purpose_cong_tac_transit": ("Mục đích: công tác / transit sân bay", ["sân bay","airport","tân sơn nhất","nội bài","phú bài","cam ranh","liên khương","ga","bến xe"]),
    "purpose_luu_tru_y_te": ("Mục đích: lưu trú y tế", ["bệnh viện","hospital","phòng khám","y khoa","chợ rẫy","tâm anh"]),
}
FACILITY_RULES = {
    "facility_group_wifi": ("Nhóm tiện ích: WiFi / Internet", ["wifi","internet","kết nối mạng"]),
    "facility_group_le_tan": ("Nhóm tiện ích: lễ tân / hỗ trợ khách", ["lễ tân","nhận phòng","check-in","check out","hành lý"]),
    "facility_group_van_chuyen": ("Nhóm tiện ích: vận chuyển / đưa đón", ["đưa đón","xe đưa đón","sân bay","taxi","thuê xe","vận chuyển"]),
    "facility_group_an_uong": ("Nhóm tiện ích: ẩm thực / bữa sáng", ["bữa sáng","nhà hàng","ẩm thực","quầy bar","cafe","ăn sáng"]),
    "facility_group_nghi_duong": ("Nhóm tiện ích: nghỉ dưỡng / thư giãn", ["hồ bơi","spa","massage","xông hơi","gym","thể thao"]),
    "facility_group_giat_ui": ("Nhóm tiện ích: giặt ủi", ["giặt","ủi","giặt ủi","laundry"]),
    "facility_group_dau_xe": ("Nhóm tiện ích: bãi đậu xe", ["đậu xe","bãi xe","bãi đậu","parking"]),
    "facility_group_gia_dinh": ("Nhóm tiện ích: gia đình / trẻ em", ["trẻ em","gia đình","phòng gia đình","family"]),
    "facility_group_cong_tac": ("Nhóm tiện ích: công tác / văn phòng", ["phòng họp","máy photocopy","máy in","văn phòng","business"]),
    "facility_group_tien_nghi_phong": ("Nhóm tiện ích: tiện nghi phòng", ["máy lạnh","tivi","tv","nước nóng","phòng tắm","bàn làm việc"]),
    "facility_group_thang_may": ("Nhóm tiện ích: thang máy / hỗ trợ di chuyển", ["thang máy","khuyết tật","wheelchair"]),
}
PURPOSE_TO_SERVICES = {
    "purpose_vui_choi_giai_tri": [("service_lich_trinh_buoi_toi","Dịch vụ gợi ý: lịch trình buổi tối"),("service_diem_checkin","Dịch vụ gợi ý: điểm check-in gần khách sạn"),("service_taxi_noi_thanh","Dịch vụ gợi ý: taxi / di chuyển nội thành")],
    "purpose_mua_sam_an_uong": [("service_food_tour","Dịch vụ gợi ý: food tour"),("service_goi_y_quan_an","Dịch vụ gợi ý: quán ăn gần khách sạn"),("service_taxi_noi_thanh","Dịch vụ gợi ý: taxi / di chuyển nội thành")],
    "purpose_tham_quan_van_hoa": [("service_city_tour","Dịch vụ gợi ý: city tour"),("service_huong_dan_vien","Dịch vụ gợi ý: hướng dẫn viên"),("service_thue_xe_tham_quan","Dịch vụ gợi ý: thuê xe tham quan")],
    "purpose_du_lich_bien_nghi_duong": [("service_tour_bien","Dịch vụ gợi ý: tour biển"),("service_thue_xe_may","Dịch vụ gợi ý: thuê xe máy"),("service_goi_y_hai_san","Dịch vụ gợi ý: gợi ý hải sản")],
    "purpose_cong_tac_transit": [("service_dua_don_san_bay","Dịch vụ gợi ý: đưa đón sân bay"),("service_checkin_nhanh","Dịch vụ gợi ý: check-in nhanh"),("service_giat_ui","Dịch vụ gợi ý: giặt ủi")],
    "purpose_luu_tru_y_te": [("service_phong_yen_tinh","Dịch vụ gợi ý: phòng yên tĩnh"),("service_giat_ui","Dịch vụ gợi ý: giặt ủi"),("service_thang_may","Dịch vụ gợi ý: thang máy")],
}

def add_basic_items(items, row):
    region = str(row.get("region", "")).strip()
    if region: add_item(items, "region_" + slug(region), f"Khu vực: {region}", "region")
    district = str(row.get("district", "")).strip()
    if district: add_item(items, "district_" + slug(district), f"Quận / khu vực: {district}", "district")
    price = str(row.get("price_level", "")).strip()
    if price: add_item(items, "price_" + slug(price), f"Mức giá: {price}", "price")
    try: rating = float(row.get("overall_rating_clean"))
    except Exception: rating = None
    if rating is not None:
        if rating >= 9: add_item(items, "rating_xuat_sac", "Rating: xuất sắc", "rating")
        elif rating >= 8: add_item(items, "rating_cao", "Rating: cao", "rating")
        elif rating >= 7: add_item(items, "rating_kha", "Rating: khá", "rating")
        else: add_item(items, "rating_trung_binh", "Rating: trung bình", "rating")
    try: review = int(row.get("review_count_clean"))
    except Exception: review = None
    if review is not None:
        if review >= 500: add_item(items, "review_rat_nhieu", "Số đánh giá: rất nhiều", "review")
        elif review >= 100: add_item(items, "review_nhieu", "Số đánh giá: nhiều", "review")
        elif review >= 30: add_item(items, "review_trung_binh", "Số đánh giá: trung bình", "review")
        else: add_item(items, "review_it", "Số đánh giá: ít", "review")
    try: star = int(float(row.get("star_rating_clean")))
    except Exception: star = None
    if star is not None:
        if star >= 5: add_item(items, "star_5_sao", "Khách sạn 5 sao", "star")
        elif star == 4: add_item(items, "star_4_sao", "Khách sạn 4 sao", "star")
        elif star == 3: add_item(items, "star_3_sao", "Khách sạn 3 sao", "star")
        elif star > 0: add_item(items, "star_duoi_3_sao", "Khách sạn dưới 3 sao", "star")

def add_purpose_items(items, row):
    text = " | ".join(str(row.get(c, "")) for c in ["tourism_tags", "nearby_text_for_app", "nearby_places_clean", "nearby_places", "general_Điểm đến phổ biến"] if pd.notna(row.get(c, "")))
    matched = []
    for code, (label, kws) in PLACE_RULES.items():
        if contains_any(text, kws):
            add_item(items, code, label, "purpose"); matched.append(code)
    return matched

def add_facility_group_items(items, row):
    text = " | ".join(str(row.get(c, "")) for c in row.index if (str(c).startswith("facility_") or str(c).startswith("general_") or c == "facilities_clean") and pd.notna(row.get(c, "")))
    matched = []
    for code, (label, kws) in FACILITY_RULES.items():
        if contains_any(text, kws):
            add_item(items, code, label, "facility_group"); matched.append(code)
    return matched

def add_raw_facility_items(items, row, limit=8):
    for f in split_items(row.get("facilities_clean", ""))[:limit]:
        add_item(items, "facility_raw_" + slug(f), f"Tiện ích cụ thể: {f}", "facility_raw")

def add_service_items(items, purposes, facilities):
    service_codes = set()
    for p in purposes:
        for code, label in PURPOSE_TO_SERVICES.get(p, []): service_codes.add((code, label))
    if "facility_group_van_chuyen" in facilities: service_codes.add(("service_dua_don_di_chuyen", "Dịch vụ gợi ý: đưa đón / di chuyển"))
    if "facility_group_giat_ui" in facilities: service_codes.add(("service_giat_ui", "Dịch vụ gợi ý: giặt ủi"))
    if "facility_group_nghi_duong" in facilities: service_codes.add(("service_spa_ho_boi", "Dịch vụ gợi ý: spa / hồ bơi"))
    if "facility_group_an_uong" in facilities: service_codes.add(("service_goi_y_an_uong", "Dịch vụ gợi ý: ăn uống"))
    for code, label in service_codes: add_item(items, code, label, "service")

def add_hotel_profile_items(items, row, purposes, facilities):
    price = str(row.get("price_level", "")).strip()
    try: rating = float(row.get("overall_rating_clean"))
    except Exception: rating = None
    try: star = float(row.get("star_rating_clean"))
    except Exception: star = None
    if rating is not None and rating >= 8.5 and price in ["Giá rẻ", "Giá trung bình"]: add_item(items, "hotel_profile_dang_tien", "Hồ sơ khách sạn: đáng tiền", "hotel_profile")
    if rating is not None and rating >= 8.5 and price == "Giá cao": add_item(items, "hotel_profile_cao_cap", "Hồ sơ khách sạn: cao cấp", "hotel_profile")
    if star is not None and star >= 4: add_item(items, "hotel_profile_tieu_chuan_cao", "Hồ sơ khách sạn: tiêu chuẩn cao", "hotel_profile")
    if "facility_group_gia_dinh" in facilities: add_item(items, "hotel_profile_phu_hop_gia_dinh", "Hồ sơ khách sạn: phù hợp gia đình", "hotel_profile")
    if "purpose_cong_tac_transit" in purposes or "facility_group_cong_tac" in facilities: add_item(items, "hotel_profile_phu_hop_cong_tac", "Hồ sơ khách sạn: phù hợp công tác", "hotel_profile")
    if "purpose_du_lich_bien_nghi_duong" in purposes: add_item(items, "hotel_profile_nghi_duong_bien", "Hồ sơ khách sạn: nghỉ dưỡng biển", "hotel_profile")

def build_transaction(row):
    items = []
    add_basic_items(items, row)
    purposes = add_purpose_items(items, row)
    facilities = add_facility_group_items(items, row)
    add_raw_facility_items(items, row)
    add_service_items(items, purposes, facilities)
    add_hotel_profile_items(items, row, purposes, facilities)
    return " | ".join(dict.fromkeys(items))

def main():
    df = load_hotels(DATA_FILE)
    print("Số khách sạn:", len(df)); print("Số cột:", len(df.columns))
    df["transaction_items"] = df.apply(build_transaction, axis=1)
    tx = df[["region", "hotel_name", "hotel_url", "transaction_items"]].copy()
    tx.to_csv(TRANSACTION_FILE, index=False, encoding="utf-8-sig")
    transactions = [split_items(x) for x in tx["transaction_items"].fillna("")]
    all_items = sorted({item for trans in transactions for item in trans})
    onehot = pd.DataFrame([{item: int(item in set(trans)) for item in all_items} for trans in transactions])
    onehot.insert(0, "region", tx["region"].values)
    onehot.insert(1, "hotel_name", tx["hotel_name"].values)
    onehot.to_csv(ONEHOT_FILE, index=False, encoding="utf-8-sig")
    pd.DataFrame(ITEM_DICT.values()).to_csv(ITEM_DICTIONARY_FILE, index=False, encoding="utf-8-sig")
    print("Đã tạo:", TRANSACTION_FILE)
    print("Đã tạo:", ONEHOT_FILE)
    print("Đã tạo:", ITEM_DICTIONARY_FILE)
    print("Số item:", len(all_items))

if __name__ == "__main__":
    main()
