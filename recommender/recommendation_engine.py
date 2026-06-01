from pathlib import Path
import re, unicodedata
import numpy as np
import pandas as pd
from recommender.utils import OUTPUT_DIR, split_items, service_suggestions_for_purpose

TRANSACTIONS_FILE = OUTPUT_DIR / "transactions.csv"
ITEM_DICTIONARY_FILE = OUTPUT_DIR / "item_dictionary.csv"
PRESENTATION_RULES_FILE = OUTPUT_DIR / "association_rules_presentation.csv"
REGION_RULES_FILE = OUTPUT_DIR / "association_rules_by_region.csv"
GLOBAL_RULES_FILE = OUTPUT_DIR / "association_rules_global.csv"

def remove_accents(text):
    text = unicodedata.normalize("NFD", str(text))
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.replace("đ", "d").replace("Đ", "D")

def slug(text):
    text = remove_accents(str(text).lower().strip())
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")

def normalize_score(series):
    series = pd.to_numeric(series, errors="coerce")
    if series.isna().all(): return pd.Series([0.0]*len(series), index=series.index)
    mn, mx = series.min(), series.max()
    if pd.isna(mn) or pd.isna(mx) or mx == mn: return pd.Series([0.5]*len(series), index=series.index)
    return (series-mn)/(mx-mn)

def parse_itemset_text(value):
    if pd.isna(value): return set()
    return set(x.strip() for x in str(value).split("|") if x.strip())

def load_item_dictionary():
    if not ITEM_DICTIONARY_FILE.exists(): return {}
    df = pd.read_csv(ITEM_DICTIONARY_FILE)
    return {row["item"]: {"label": row.get("label", row["item"]), "group": row.get("group", "")} for _, row in df.iterrows()}

def item_label(item, item_dict): return item_dict.get(item, {}).get("label", item)
def item_group(item, item_dict): return item_dict.get(item, {}).get("group", "")

PURPOSE_TO_ITEM = {
    "Vui chơi / giải trí": "purpose_vui_choi_giai_tri",
    "Mua sắm / ăn uống": "purpose_mua_sam_an_uong",
    "Tham quan văn hóa / di tích": "purpose_tham_quan_van_hoa",
    "Du lịch biển / nghỉ dưỡng": "purpose_du_lich_bien_nghi_duong",
    "Công tác / transit sân bay": "purpose_cong_tac_transit",
    "Lưu trú y tế": "purpose_luu_tru_y_te",
}
BUDGET_TO_ITEM = {"Giá rẻ":"price_gia_re", "Giá trung bình":"price_gia_trung_binh", "Giá cao":"price_gia_cao"}
STYLE_TO_ITEMS = {
    "Không ưu tiên đặc biệt": [],
    "Đáng tiền": ["hotel_profile_dang_tien", "rating_cao"],
    "Gần điểm du lịch": [],
    "Tiện nghi tốt": ["facility_group_tien_nghi_phong", "rating_cao"],
    "Phù hợp gia đình": ["hotel_profile_phu_hop_gia_dinh", "facility_group_gia_dinh"],
    "Phù hợp công tác": ["hotel_profile_phu_hop_cong_tac", "facility_group_cong_tac"],
    "Nghỉ dưỡng": ["hotel_profile_nghi_duong_bien", "facility_group_nghi_duong"],
}

def build_user_items(region, purpose, budget, travel_style):
    items = []
    if region: items.append("region_" + slug(region))
    if purpose in PURPOSE_TO_ITEM: items.append(PURPOSE_TO_ITEM[purpose])
    if budget in BUDGET_TO_ITEM: items.append(BUDGET_TO_ITEM[budget])
    items.extend(STYLE_TO_ITEMS.get(travel_style, []))
    return set(items)

def load_rules_for_region(region):
    parts = []
    if PRESENTATION_RULES_FILE.exists(): parts.append(pd.read_csv(PRESENTATION_RULES_FILE))
    if REGION_RULES_FILE.exists():
        rr = pd.read_csv(REGION_RULES_FILE)
        if "region" in rr.columns: rr = rr[rr["region"] == region]
        parts.append(rr)
    if GLOBAL_RULES_FILE.exists(): parts.append(pd.read_csv(GLOBAL_RULES_FILE))
    if not parts: return pd.DataFrame()
    rules = pd.concat(parts, ignore_index=True)
    return rules.drop_duplicates(subset=["antecedents_text","consequents_text"], keep="first")

def activate_rules(rules, user_items, max_rules=8):
    if rules.empty or not user_items: return pd.DataFrame()
    data = rules.copy(); scores = []
    for _, row in data.iterrows():
        ant = parse_itemset_text(row.get("antecedents_text", ""))
        con = parse_itemset_text(row.get("consequents_text", ""))
        if not ant: scores.append(0); continue
        overlap = len(ant & user_items)
        score = 1.0 if ant.issubset(user_items) else (overlap / len(ant) * 0.7 if overlap > 0 else 0)
        if any(str(x).startswith("service_") for x in con): score += 0.10
        if any(str(x).startswith("hotel_profile_") for x in con): score += 0.08
        if any(str(x).startswith("facility_group_") for x in con): score += 0.06
        try:
            score += float(row.get("confidence",0))*0.15
            score += min(float(row.get("lift",0)),3)*0.03
        except Exception: pass
        scores.append(score)
    data["activation_score"] = scores
    data = data[data["activation_score"] > 0].copy()
    return data.sort_values(["activation_score","confidence","lift"], ascending=False).head(max_rules) if not data.empty else data

def infer_items_from_rules(activated_rules):
    inferred = set()
    for _, row in activated_rules.iterrows(): inferred |= parse_itemset_text(row.get("consequents_text", ""))
    return inferred

def summarize_inferred_items(inferred_items, item_dict):
    result = {"services": [], "facilities": [], "profiles": [], "purposes": [], "others": []}
    for item in inferred_items:
        group, label = item_group(item, item_dict), item_label(item, item_dict)
        if group == "service" or item.startswith("service_"): result["services"].append(label)
        elif group == "facility_group" or item.startswith("facility_group_"): result["facilities"].append(label)
        elif group == "hotel_profile" or item.startswith("hotel_profile_"): result["profiles"].append(label)
        elif group == "purpose" or item.startswith("purpose_"): result["purposes"].append(label)
        else: result["others"].append(label)
    for k in result: result[k] = sorted(list(dict.fromkeys(result[k])))
    return result

FALLBACK_BY_PURPOSE = {
    "Vui chơi / giải trí": {"services":["Dịch vụ gợi ý: lịch trình buổi tối","Dịch vụ gợi ý: điểm check-in gần khách sạn","Dịch vụ gợi ý: taxi / di chuyển nội thành"], "facilities":["Nhóm tiện ích: WiFi / Internet","Nhóm tiện ích: lễ tân / hỗ trợ khách","Nhóm tiện ích: vận chuyển / đưa đón"], "profiles":["Hồ sơ khách sạn: đáng tiền"]},
    "Mua sắm / ăn uống": {"services":["Dịch vụ gợi ý: food tour","Dịch vụ gợi ý: quán ăn gần khách sạn","Dịch vụ gợi ý: taxi / di chuyển nội thành"], "facilities":["Nhóm tiện ích: WiFi / Internet","Nhóm tiện ích: ẩm thực / bữa sáng","Nhóm tiện ích: vận chuyển / đưa đón"], "profiles":["Hồ sơ khách sạn: đáng tiền"]},
    "Tham quan văn hóa / di tích": {"services":["Dịch vụ gợi ý: city tour","Dịch vụ gợi ý: hướng dẫn viên","Dịch vụ gợi ý: thuê xe tham quan"], "facilities":["Nhóm tiện ích: WiFi / Internet","Nhóm tiện ích: lễ tân / hỗ trợ khách","Nhóm tiện ích: vận chuyển / đưa đón"], "profiles":["Hồ sơ khách sạn: đáng tiền"]},
    "Du lịch biển / nghỉ dưỡng": {"services":["Dịch vụ gợi ý: tour biển","Dịch vụ gợi ý: thuê xe máy","Dịch vụ gợi ý: gợi ý hải sản"], "facilities":["Nhóm tiện ích: nghỉ dưỡng / thư giãn","Nhóm tiện ích: ẩm thực / bữa sáng","Nhóm tiện ích: bãi đậu xe"], "profiles":["Hồ sơ khách sạn: nghỉ dưỡng biển"]},
    "Công tác / transit sân bay": {"services":["Dịch vụ gợi ý: đưa đón sân bay","Dịch vụ gợi ý: check-in nhanh","Dịch vụ gợi ý: giặt ủi"], "facilities":["Nhóm tiện ích: WiFi / Internet","Nhóm tiện ích: vận chuyển / đưa đón","Nhóm tiện ích: công tác / văn phòng"], "profiles":["Hồ sơ khách sạn: phù hợp công tác"]},
    "Lưu trú y tế": {"services":["Dịch vụ gợi ý: phòng yên tĩnh","Dịch vụ gợi ý: giặt ủi","Dịch vụ gợi ý: thang máy"], "facilities":["Nhóm tiện ích: thang máy / hỗ trợ di chuyển","Nhóm tiện ích: giặt ủi","Nhóm tiện ích: lễ tân / hỗ trợ khách"], "profiles":["Hồ sơ khách sạn: đáng tiền"]},
}
def fallback_summary(purpose): return FALLBACK_BY_PURPOSE.get(purpose, {"services": service_suggestions_for_purpose(purpose), "facilities": [], "profiles": [], "purposes": [], "others": []})
def load_transactions(): return pd.read_csv(TRANSACTIONS_FILE) if TRANSACTIONS_FILE.exists() else pd.DataFrame()

def smart_recommend_hotels(df, selected_region, selected_purpose, selected_budget, travel_style, top_n=8):
    item_dict = load_item_dictionary()
    user_items = build_user_items(selected_region, selected_purpose, selected_budget, travel_style)
    rules = load_rules_for_region(selected_region)
    activated_rules = activate_rules(rules, user_items, max_rules=8)
    inferred_items = infer_items_from_rules(activated_rules)
    inferred_summary = summarize_inferred_items(inferred_items, item_dict)
    if not inferred_summary["services"] and not inferred_summary["facilities"] and not inferred_summary["profiles"]: inferred_summary = fallback_summary(selected_purpose)
    data = df[df["region"] == selected_region].copy() if selected_region else df.copy()
    if data.empty: return data, activated_rules, inferred_summary, user_items
    tx = load_transactions()
    data = data.merge(tx[["hotel_name","hotel_url","transaction_items"]], on=["hotel_name","hotel_url"], how="left") if not tx.empty else data.assign(transaction_items="")
    rating_norm, review_norm = normalize_score(data["overall_rating_clean"]), normalize_score(data["review_count_clean"])
    label_to_item = {v["label"]: k for k,v in item_dict.items()}
    recommended_items = set(user_items) | set(inferred_items)
    for group in ["services","facilities","profiles"]:
        for label in inferred_summary.get(group, []):
            if label in label_to_item: recommended_items.add(label_to_item[label])
    rule_scores=[]; user_scores=[]; budget_scores=[]; reasons=[]; services=[]; matched_rules=[]
    for _, row in data.iterrows():
        trans = parse_itemset_text(row.get("transaction_items", ""))
        rule_scores.append(len(trans & recommended_items) / max(len(recommended_items),1) if recommended_items else 0)
        user_scores.append(len(trans & user_items) / max(len(user_items),1) if user_items else 0)
        bitem = BUDGET_TO_ITEM.get(selected_budget, "")
        budget_scores.append(1.0 if bitem and bitem in trans else (0.7 if not selected_budget else 0.0))
        rs = [f"Thuộc khu vực {selected_region}", f"Phù hợp với chuyến đi: {selected_purpose}"]
        if selected_budget: rs.append(f"Ngân sách mong muốn: {selected_budget}")
        if travel_style != "Không ưu tiên đặc biệt": rs.append(f"Phong cách ưu tiên: {travel_style}")
        matched_labels = [item_label(i, item_dict) for i in sorted(trans & recommended_items)]
        if matched_labels: rs.append("Khớp với đặc điểm hệ thống suy ra: " + ", ".join(matched_labels[:4]))
        reasons.append(" | ".join(rs))
        services.append(" | ".join(inferred_summary.get("services", [])))
        exps=[]
        for _, rr in activated_rules.iterrows():
            if parse_itemset_text(rr.get("consequents_text", "")) & trans:
                exp=str(rr.get("explanation","")).strip()
                if exp: exps.append(exp)
        matched_rules.append(" | ".join(exps[:3]))
    data["rule_score"] = rule_scores; data["user_need_score"] = user_scores; data["budget_score"] = budget_scores
    data["rating_score_norm"] = rating_norm; data["review_score_norm"] = review_norm
    data["recommend_score"] = 0.45*data["rule_score"] + 0.20*data["user_need_score"] + 0.15*data["rating_score_norm"] + 0.10*data["budget_score"] + 0.10*data["review_score_norm"]
    data["recommend_percent"] = (data["recommend_score"]*100).round(1)
    data["reason"] = reasons; data["suggested_services"] = services; data["matched_rules"] = matched_rules
    data = data.sort_values(["recommend_score","overall_rating_clean","review_count_clean"], ascending=False)
    return data.head(top_n), activated_rules, inferred_summary, user_items

def recommend_hotels(df, selected_region, selected_purpose, selected_budget, selected_facilities=None, top_n=10):
    recs, _, _, _ = smart_recommend_hotels(df, selected_region, selected_purpose, selected_budget, "Không ưu tiên đặc biệt", top_n)
    return recs
