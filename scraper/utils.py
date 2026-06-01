import pandas as pd
import os


def save_to_csv(data, output_path):

    df = pd.DataFrame(data)

    os.makedirs(
        os.path.dirname(output_path),
        exist_ok=True
    )

    df.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"Đã lưu: {output_path}")