from pathlib import Path
import pandas as pd
from mlxtend.frequent_patterns import fpgrowth, association_rules

ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT_DIR / "data" / "output"
ONEHOT_FILE = OUTPUT_DIR / "onehot.csv"
ITEM_DICTIONARY_FILE = OUTPUT_DIR / "item_dictionary.csv"
GLOBAL_RULES_FILE = OUTPUT_DIR / "association_rules_global.csv"
REGION_RULES_FILE = OUTPUT_DIR / "association_rules_by_region.csv"
PURPOSE_RULES_FILE = OUTPUT_DIR / "association_rules_by_purpose.csv"
PRESENTATION_RULES_FILE = OUTPUT_DIR / "association_rules_presentation.csv"

MAX_LEN = 3
GLOBAL_MIN_SUPPORT = 0.05
GLOBAL_MIN_CONFIDENCE = 0.35
GLOBAL_MIN_LIFT = 1.0
MAX_ITEMS_GLOBAL = 160
MAX_ITEMS_REGION = 110
MAX_ITEMS_PURPOSE = 120
USEFUL_CONSEQUENT_PREFIXES = ("service_", "hotel_profile_", "facility_group_", "purpose_")

def load_item_dictionary():
    if not ITEM_DICTIONARY_FILE.exists(): return {}
    df = pd.read_csv(ITEM_DICTIONARY_FILE)
    return {row["item"]: {"label": row.get("label", row["item"]), "group": row.get("group", "")} for _, row in df.iterrows()}
ITEM_DICT = load_item_dictionary()

def get_label(item): return ITEM_DICT.get(item, {}).get("label", item)
def get_group(item): return ITEM_DICT.get(item, {}).get("group", "")
def itemset_to_text(itemset): return " | ".join(sorted(list(itemset)))
def itemset_to_label(itemset): return " + ".join(get_label(i) for i in sorted(list(itemset)))
def itemset_groups(itemset): return " + ".join(sorted(set(get_group(i) for i in itemset if get_group(i))))

def prepare_onehot(data, min_support, max_items):
    meta = [c for c in ["region", "hotel_name"] if c in data.columns]
    onehot = data.drop(columns=meta, errors="ignore")
    onehot = onehot.apply(pd.to_numeric, errors="coerce").fillna(0).clip(0, 1)
    onehot = onehot.loc[:, onehot.sum(axis=0) > 0]
    if onehot.empty: return onehot
    item_support = onehot.mean(axis=0)
    item_support = item_support[item_support >= min_support]
    if item_support.empty: return pd.DataFrame()
    keep_cols = item_support.sort_values(ascending=False).head(max_items).index
    return onehot[keep_cols].astype(bool)

def has_useful_consequent(itemset):
    return any(str(i).startswith(USEFUL_CONSEQUENT_PREFIXES) for i in itemset)

def is_not_too_trivial(row):
    ant_groups = set(get_group(x) for x in row["antecedents"])
    con_groups = set(get_group(x) for x in row["consequents"])
    return not (ant_groups == con_groups and len(ant_groups) == 1)

def add_readable_columns(rules, source_name):
    if rules.empty: return rules
    rules = rules.copy()
    rules["antecedents_text"] = rules["antecedents"].apply(itemset_to_text)
    rules["consequents_text"] = rules["consequents"].apply(itemset_to_text)
    rules["antecedents_label"] = rules["antecedents"].apply(itemset_to_label)
    rules["consequents_label"] = rules["consequents"].apply(itemset_to_label)
    rules["antecedent_groups"] = rules["antecedents"].apply(itemset_groups)
    rules["consequent_groups"] = rules["consequents"].apply(itemset_groups)
    rules["rule_source"] = source_name
    rules["explanation"] = rules.apply(lambda r: f"Nếu {r['antecedents_label']} thì thường đi kèm {r['consequents_label']} (support={round(r['support'],3)}, confidence={round(r['confidence'],3)}, lift={round(r['lift'],3)}).", axis=1)
    return rules[["rule_source","antecedents_text","consequents_text","antecedents_label","consequents_label","antecedent_groups","consequent_groups","support","confidence","lift","explanation"]].copy()

def mine_rules_from_df(data, min_support, min_confidence, min_lift, max_len, max_items, source_name):
    onehot = prepare_onehot(data, min_support, max_items)
    if onehot.empty or len(onehot.columns) < 2: return pd.DataFrame()
    print(f"Đang chạy FP-Growth: source={source_name}, rows={len(onehot)}, items={len(onehot.columns)}, min_support={min_support}, max_len={max_len}")
    frequent = fpgrowth(onehot, min_support=min_support, use_colnames=True, max_len=max_len)
    if frequent.empty: return pd.DataFrame()
    rules = association_rules(frequent, metric="confidence", min_threshold=min_confidence)
    if rules.empty: return pd.DataFrame()
    rules = rules[rules["lift"] >= min_lift].copy()
    rules = rules[rules["consequents"].apply(has_useful_consequent)].copy()
    rules = rules[rules.apply(is_not_too_trivial, axis=1)].copy()
    if rules.empty: return pd.DataFrame()
    rules = rules.sort_values(["lift", "confidence", "support"], ascending=False)
    return add_readable_columns(rules, source_name)

def get_region_support(n):
    if n >= 100: return 0.05
    if n >= 50: return 0.08
    if n >= 25: return 0.12
    return 0.20

def main():
    if not ONEHOT_FILE.exists():
        raise FileNotFoundError(f"Không thấy file: {ONEHOT_FILE}. Hãy chạy python mining/build_transactions.py trước.")
    df = pd.read_csv(ONEHOT_FILE)
    print("Đã đọc:", ONEHOT_FILE, "rows=", len(df), "cols=", len(df.columns))
    global_rules = mine_rules_from_df(df, GLOBAL_MIN_SUPPORT, GLOBAL_MIN_CONFIDENCE, GLOBAL_MIN_LIFT, MAX_LEN, MAX_ITEMS_GLOBAL, "global")
    global_rules.to_csv(GLOBAL_RULES_FILE, index=False, encoding="utf-8-sig")
    region_parts = []
    if "region" in df.columns:
        for region, group in df.groupby("region"):
            if len(group) < 5: continue
            rules = mine_rules_from_df(group, get_region_support(len(group)), 0.35, 1.0, MAX_LEN, MAX_ITEMS_REGION, f"region:{region}")
            if not rules.empty:
                rules.insert(0, "region", region); region_parts.append(rules)
    region_rules = pd.concat(region_parts, ignore_index=True) if region_parts else pd.DataFrame()
    region_rules.to_csv(REGION_RULES_FILE, index=False, encoding="utf-8-sig")
    purpose_parts = []
    for purpose_col in [c for c in df.columns if str(c).startswith("purpose_")]:
        group = df[df[purpose_col] == 1].copy()
        if len(group) < 10: continue
        rules = mine_rules_from_df(group, 0.08 if len(group)>=50 else 0.12, 0.35, 1.0, MAX_LEN, MAX_ITEMS_PURPOSE, f"purpose:{purpose_col}")
        if not rules.empty:
            rules.insert(0, "purpose_item", purpose_col); rules.insert(1, "purpose_label", get_label(purpose_col)); purpose_parts.append(rules)
    purpose_rules = pd.concat(purpose_parts, ignore_index=True) if purpose_parts else pd.DataFrame()
    purpose_rules.to_csv(PURPOSE_RULES_FILE, index=False, encoding="utf-8-sig")
    final_parts = [x.head(80) for x in [global_rules, region_rules, purpose_rules] if not x.empty]
    presentation = pd.concat(final_parts, ignore_index=True).sort_values(["lift","confidence","support"], ascending=False).head(120) if final_parts else pd.DataFrame()
    presentation.to_csv(PRESENTATION_RULES_FILE, index=False, encoding="utf-8-sig")
    print("Đã tạo luật:", GLOBAL_RULES_FILE, REGION_RULES_FILE, PURPOSE_RULES_FILE, PRESENTATION_RULES_FILE)
    print("Số luật thuyết trình:", len(presentation))

if __name__ == "__main__":
    main()
