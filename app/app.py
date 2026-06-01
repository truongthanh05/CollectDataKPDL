import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from recommender.utils import REGIONS, REGION_IMAGE_MAP, OUTPUT_DIR, load_hotels, split_items, get_all_facilities, format_vnd
from recommender.recommendation_engine import smart_recommend_hotels

st.set_page_config(page_title="Gợi ý khách sạn du lịch", page_icon="🏨", layout="wide")

def load_css():
    st.markdown("""
    <style>
    html, body, .stApp, [data-testid="stAppViewContainer"] {background:#F4F8FF!important;color:#0F172A!important;}
    [data-testid="stHeader"] {background:rgba(244,248,255,.92)!important;}
    .block-container {padding-top:1.2rem;padding-bottom:2.5rem;max-width:1320px;}
    h1,h2,h3,h4,h5,h6,p,span,label,div {color:#0F172A;}
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {background:#FFF!important;color:#0F172A!important;border:1px solid #D7E4F5!important;border-radius:14px!important;}
    div[data-baseweb="select"] span, div[data-baseweb="input"] input {color:#0F172A!important;}
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] {background:#FFF!important;color:#0F172A!important;border:1px solid #D7E4F5!important;}
    li[role="option"], div[role="option"] {background:#FFF!important;color:#0F172A!important;}
    li[role="option"]:hover, div[role="option"]:hover {background:#EAF4FF!important;color:#0B5CAD!important;}
    div.stButton > button {background:#FFF!important;color:#0B5CAD!important;border:1px solid #CFE3FF!important;border-radius:14px!important;font-weight:750!important;min-height:42px;}
    div.stButton > button:hover {background:#EAF4FF!important;color:#064A8E!important;border-color:#8DC5FF!important;}
    div[data-testid="stMetric"] {background:#FFF;border:1px solid #DFEAF7;border-radius:18px;padding:14px 16px;box-shadow:0 8px 24px rgba(15,23,42,.06);}
    .stTabs [data-baseweb="tab"] {background:#FFF;border:1px solid #D7E4F5;border-radius:14px;padding:10px 18px;color:#0F172A;font-weight:750;}
    .stTabs [aria-selected="true"] {background:#E8F3FF!important;color:#0B5CAD!important;border-color:#9BD0FF!important;}
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def get_data():
    return load_hotels()

def get_region_image_path(region):
    image_name = REGION_IMAGE_MAP.get(region, "")
    image_path = ROOT_DIR / "assets" / "regions" / image_name
    return image_path if image_path.exists() else None

def safe_str(value):
    if pd.isna(value): return ""
    return str(value).strip()

def get_short_address(address):
    address = safe_str(address)
    if not address: return "Không có địa chỉ"
    parts = [x.strip() for x in address.split(",") if x.strip()]
    return ", ".join(parts[:4]) if len(parts) >= 4 else address

def get_nearby_items(row):
    value = row.get("nearby_text_for_app", "")
    if not safe_str(value): value = row.get("nearby_places_clean", "")
    if not safe_str(value): value = row.get("nearby_places", "")
    return split_items(value)

def get_facility_items(row): return split_items(row.get("facilities_clean", ""))
def get_tourism_items(row): return split_items(row.get("tourism_tags", ""))

def get_price_text(row):
    price_clean = row.get("price_clean", None)
    if pd.notna(price_clean): return format_vnd(price_clean)
    price = safe_str(row.get("price", ""))
    return price if price else "N/A"

def get_rating_text(row):
    value = row.get("overall_rating_clean", None)
    if pd.notna(value): return str(value)
    value = safe_str(row.get("overall_rating", ""))
    return value if value else "N/A"

def get_star_text(row):
    value = row.get("star_rating_clean", None)
    if pd.notna(value): return str(value)
    value = safe_str(row.get("star_rating", ""))
    return value if value else "N/A"

def show_items_as_text(items, limit=5):
    items = [safe_str(x) for x in items if safe_str(x)]
    if not items: st.caption("Chưa có dữ liệu")
    else: st.caption(" • ".join(items[:limit]))

def show_region_home(df):
    st.title("Website gợi ý khách sạn theo mục đích du lịch")
    st.write("Chọn khu vực để bắt đầu tìm khách sạn và dịch vụ du lịch phù hợp.")
    cols = st.columns(3)
    for idx, region in enumerate(REGIONS):
        region_df = df[df["region"] == region]
        count = len(region_df)
        avg_price = format_vnd(region_df["price_clean"].mean()) if count > 0 else "N/A"
        with cols[idx % 3]:
            with st.container(border=True):
                image_path = get_region_image_path(region)
                if image_path: st.image(str(image_path), use_container_width=True)
                st.subheader(f"Khách sạn ở {region}")
                st.caption(f"{count} khách sạn · Giá trung bình {avg_price}")
                if st.button(f"Chọn {region}", key=f"choose_{region}", use_container_width=True, disabled=count == 0):
                    st.session_state["selected_region"] = region
                    st.rerun()

def show_dashboard(df_region, region):
    st.header(f"Tổng quan khách sạn ở {region}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Số khách sạn", len(df_region))
    c2.metric("Giá trung bình", format_vnd(df_region["price_clean"].mean()))
    c3.metric("Rating trung bình", round(df_region["overall_rating_clean"].mean(), 2))
    c4.metric("Review trung bình", int(df_region["review_count_clean"].fillna(0).mean()))
    col1, col2 = st.columns(2)
    with col1:
        fig = px.histogram(df_region, x="price_level", title="Phân bố mức giá", color_discrete_sequence=["#3B82F6"])
        fig.update_layout(template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.histogram(df_region, x="star_rating_clean", title="Phân bố số sao", color_discrete_sequence=["#06B6D4"])
        fig.update_layout(template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    st.subheader("Top tiện ích phổ biến")
    fac_counts = {}
    for value in df_region["facilities_clean"].fillna(""):
        for item in split_items(value): fac_counts[item] = fac_counts.get(item, 0) + 1
    if fac_counts:
        top_fac = pd.DataFrame(fac_counts.items(), columns=["facility", "count"]).sort_values("count", ascending=False).head(12)
        fig = px.bar(top_fac, x="count", y="facility", orientation="h", title="Top 12 tiện ích phổ biến", color_discrete_sequence=["#0EA5E9"])
        fig.update_layout(template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    st.subheader("Mục đích du lịch phổ biến")
    tag_counts = {}
    for value in df_region["tourism_tags"].fillna(""):
        for item in split_items(value): tag_counts[item] = tag_counts.get(item, 0) + 1
    if tag_counts:
        top_tag = pd.DataFrame(tag_counts.items(), columns=["tourism_tag", "count"]).sort_values("count", ascending=False).head(10)
        fig = px.bar(top_tag, x="count", y="tourism_tag", orientation="h", title="Top mục đích du lịch", color_discrete_sequence=["#F97316"])
        fig.update_layout(template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

def hotel_card(row, show_score=False):
    hotel_name = safe_str(row.get("hotel_name", "Không rõ tên"))
    region = safe_str(row.get("region", ""))
    address = get_short_address(row.get("address", ""))
    price_text = get_price_text(row)
    rating_text = get_rating_text(row)
    star_text = get_star_text(row)
    review_text = safe_str(row.get("review_count_clean", row.get("review_count", "")))
    hotel_url = safe_str(row.get("hotel_url", ""))
    tourism_items, facility_items, nearby_items = get_tourism_items(row), get_facility_items(row), get_nearby_items(row)
    with st.container(border=True):
        col_img, col_info, col_price = st.columns([1.25, 3.2, 1.2])
        with col_img:
            image_path = get_region_image_path(region)
            if image_path: st.image(str(image_path), use_container_width=True)
            else: st.info("Ảnh khu vực")
        with col_info:
            st.subheader(hotel_name)
            st.caption(address)
            m1, m2, m3 = st.columns(3)
            m1.write(f"Rating: **{rating_text}**")
            m2.write(f"Sao: **{star_text}**")
            m3.write(f"Đánh giá: **{review_text}**")
            st.write("**Mục đích phù hợp**"); show_items_as_text(tourism_items, limit=3)
            st.write("**Tiện ích nổi bật**"); show_items_as_text(facility_items, limit=5)
            st.write("**Địa điểm gần**"); show_items_as_text(nearby_items, limit=4)
        with col_price:
            if show_score and "recommend_percent" in row: st.success(f"Phù hợp {row.get('recommend_percent')}%")
            st.caption("Giá tham khảo")
            st.markdown(f"### {price_text}")
            st.caption("/ phòng / đêm")
            if hotel_url: st.link_button("Xem chi tiết", hotel_url, use_container_width=True)
        with st.expander("Xem thêm thông tin"):
            st.write("**Địa chỉ đầy đủ:**", row.get("address", ""))
            st.write("**Toàn bộ tiện ích:**", ", ".join(facility_items) if facility_items else "Không có")
            st.write("**Toàn bộ địa điểm gần:**", ", ".join(nearby_items) if nearby_items else "Không có")
            reason = safe_str(row.get("reason", ""))
            if reason:
                st.write("**Vì sao phù hợp:**")
                for item in reason.split("|"):
                    if item.strip(): st.write("- " + item.strip())
            services = safe_str(row.get("suggested_services", ""))
            if services:
                st.write("**Dịch vụ gợi ý:**")
                for item in split_items(services): st.write("- " + item)
            matched_rules = safe_str(row.get("matched_rules", ""))
            if matched_rules:
                st.write("**Một số luật liên quan:**")
                for item in matched_rules.split("|"):
                    if item.strip(): st.write("- " + item.strip())

def show_explorer(df_region, region):
    st.header(f"Khám phá khách sạn ở {region}")
    col1, col2 = st.columns(2)
    with col1:
        price_levels = [x for x in df_region["price_level"].dropna().unique() if str(x).strip()]
        selected_price = st.selectbox("Mức giá", ["Tất cả"] + sorted(price_levels))
    with col2:
        min_rating = st.slider("Rating tối thiểu", 0.0, 10.0, 0.0, 0.1)
    selected_facilities = st.multiselect("Tiện ích cần có", get_all_facilities(df_region))
    result = df_region.copy()
    if selected_price != "Tất cả": result = result[result["price_level"] == selected_price]
    result = result[result["overall_rating_clean"].fillna(0) >= min_rating]
    if selected_facilities:
        keys = [x.lower() for x in selected_facilities]
        result = result[result["facilities_clean"].fillna("").apply(lambda t: all(k in " ".join(split_items(t)).lower() for k in keys))]
    result = result.sort_values(["overall_rating_clean", "review_count_clean"], ascending=False)
    st.subheader(f"Tìm thấy {len(result)} khách sạn")
    for _, row in result.head(30).iterrows(): hotel_card(row)

def show_smart_recommendation(df, selected_region):
    st.header("Tìm khách sạn phù hợp với chuyến đi của bạn")
    st.write("Bạn chỉ cần mô tả nhu cầu. Hệ thống sẽ dùng quy luật khai phá từ dữ liệu để suy ra dịch vụ, tiện ích và kiểu khách sạn phù hợp.")
    purposes = ["Vui chơi / giải trí", "Mua sắm / ăn uống", "Tham quan văn hóa / di tích", "Du lịch biển / nghỉ dưỡng", "Công tác / transit sân bay", "Lưu trú y tế"]
    styles = ["Không ưu tiên đặc biệt", "Đáng tiền", "Gần điểm du lịch", "Tiện nghi tốt", "Phù hợp gia đình", "Phù hợp công tác", "Nghỉ dưỡng"]
    col1, col2 = st.columns(2)
    with col1: selected_purpose = st.selectbox("Bạn đi với mục đích gì?", purposes)
    with col2: travel_style = st.selectbox("Bạn ưu tiên điều gì?", styles)
    col3, col4 = st.columns(2)
    with col3:
        budget = st.selectbox("Ngân sách mong muốn", ["", "Giá rẻ", "Giá trung bình", "Giá cao"], format_func=lambda x: "Không quan trọng" if x == "" else x)
    with col4: top_n = st.slider("Số khách sạn muốn xem", 3, 15, 5)
    if st.button("Tìm khách sạn phù hợp", type="primary", use_container_width=True):
        recs, activated_rules, inferred_summary, user_items = smart_recommend_hotels(df, selected_region, selected_purpose, budget, travel_style, top_n)
        st.divider()
        st.subheader("Hệ thống hiểu nhu cầu của bạn")
        budget_text = budget if budget else "không giới hạn ngân sách"
        st.info(f"Bạn đang tìm khách sạn ở {selected_region}, mục đích {selected_purpose.lower()}, ưu tiên {travel_style.lower()}, với ngân sách {budget_text.lower()}.")
        st.subheader("Gợi ý thêm cho chuyến đi")
        s1, s2, s3 = st.columns(3)
        with s1:
            st.write("**Dịch vụ nên đi kèm**")
            for item in inferred_summary.get("services", [])[:6]: st.write("- " + item.replace("Dịch vụ gợi ý: ", ""))
        with s2:
            st.write("**Tiện ích nên ưu tiên**")
            for item in inferred_summary.get("facilities", [])[:6]: st.write("- " + item.replace("Nhóm tiện ích: ", ""))
        with s3:
            st.write("**Kiểu khách sạn phù hợp**")
            for item in inferred_summary.get("profiles", [])[:6]: st.write("- " + item.replace("Hồ sơ khách sạn: ", ""))
        with st.expander("Xem các luật được hệ thống sử dụng"):
            if activated_rules.empty:
                st.write("Chưa có luật đủ mạnh cho lựa chọn này. Hệ thống dùng quy tắc dự phòng theo mục đích chuyến đi.")
            else:
                for idx, (_, rule) in enumerate(activated_rules.head(8).iterrows(), start=1):
                    st.write(f"**Luật {idx}**")
                    st.write(rule.get("explanation", ""))
                    st.caption(f"Confidence: {round(rule.get('confidence', 0), 3)} | Lift: {round(rule.get('lift', 0), 3)}")
                    st.write("---")
        st.subheader("Khách sạn phù hợp nhất")
        if recs.empty: st.warning("Không tìm thấy khách sạn phù hợp."); return
        for _, row in recs.iterrows(): hotel_card(row, show_score=True)

def show_rules(selected_region):
    st.header(f"Luật kết hợp - {selected_region}")
    files = [OUTPUT_DIR / "association_rules_presentation.csv", OUTPUT_DIR / "association_rules_by_region.csv", OUTPUT_DIR / "association_rules_global.csv"]
    rules = pd.DataFrame()
    for f in files:
        if f.exists():
            rules = pd.read_csv(f)
            break
    if rules.empty:
        st.warning("Chưa có file luật. Hãy chạy build_transactions.py và apriori_rules.py trước."); return
    col1, col2 = st.columns(2)
    with col1: min_conf = st.slider("Confidence tối thiểu", 0.0, 1.0, 0.35, 0.05)
    with col2: min_lift = st.slider("Lift tối thiểu", 0.0, 5.0, 1.0, 0.1)
    filtered = rules[(rules["confidence"] >= min_conf) & (rules["lift"] >= min_lift)].copy()
    st.write(f"Số luật: **{len(filtered)}**")
    cols = [c for c in ["antecedents_label", "consequents_label", "support", "confidence", "lift", "explanation"] if c in filtered.columns]
    st.dataframe(filtered.sort_values(["lift", "confidence"], ascending=False)[cols], use_container_width=True)

def main():
    load_css()
    try: df = get_data()
    except Exception as e: st.error(str(e)); st.stop()
    if "selected_region" not in st.session_state: st.session_state["selected_region"] = None
    selected_region = st.session_state["selected_region"]
    if selected_region is None:
        show_region_home(df); return
    top_col1, top_col2 = st.columns([5, 1])
    with top_col1:
        st.title(f"Khách sạn ở {selected_region}")
        st.caption("Khám phá khách sạn, tìm gợi ý theo nhu cầu và xem các luật khai phá dữ liệu.")
    with top_col2:
        st.write("")
        if st.button("Quay lại", use_container_width=True):
            st.session_state["selected_region"] = None; st.rerun()
    df_region = df[df["region"] == selected_region].copy()
    if df_region.empty: st.warning(f"Không có dữ liệu cho region: {selected_region}"); return
    tab1, tab2, tab3, tab4 = st.tabs(["Tổng quan", "Khám phá", "Tìm khách sạn phù hợp", "Luật kết hợp"])
    with tab1: show_dashboard(df_region, selected_region)
    with tab2: show_explorer(df_region, selected_region)
    with tab3: show_smart_recommendation(df, selected_region)
    with tab4: show_rules(selected_region)

if __name__ == "__main__":
    main()
