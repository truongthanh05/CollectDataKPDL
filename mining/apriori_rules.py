import pandas as pd

from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori
from mlxtend.frequent_patterns import association_rules


def generate_rules():

    df = pd.read_csv("../data/processed/cleaned_hotels.csv")

    # chuyển từng dòng thành transaction
    transactions = []

    for _, row in df.iterrows():

        transaction = [
            row["hotel_type"],
            row["trip_type"],
            row["meal_plan"],
            row["activity"],
            row["nearby_place"]
        ]

        transactions.append(transaction)

    # encode dữ liệu
    te = TransactionEncoder()

    te_array = te.fit(transactions).transform(transactions)

    transaction_df = pd.DataFrame(
        te_array,
        columns=te.columns_
    )

    # tìm frequent itemsets
    frequent_itemsets = apriori(
        transaction_df,
        min_support=0.2,
        use_colnames=True
    )

    # sinh luật kết hợp
    rules = association_rules(
        frequent_itemsets,
        metric="confidence",
        min_threshold=0.5
    )

    print(rules[[
        "antecedents",
        "consequents",
        "support",
        "confidence",
        "lift"
    ]])


if __name__ == "__main__":
    generate_rules()