import pandas as pd
import matplotlib.pyplot as plt


def plot_trip_type_chart():

    df = pd.read_csv(
        "../data/processed/cleaned_hotels.csv"
    )

    counts = df["trip_type"].value_counts()

    plt.figure(figsize=(8, 5))

    counts.plot(kind="bar")

    plt.title("Phân bố loại chuyến đi")

    plt.xlabel("Trip Type")

    plt.ylabel("Số lượng")

    plt.show()


if __name__ == "__main__":
    plot_trip_type_chart()