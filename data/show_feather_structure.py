import pandas as pd

# If your .feather files are in a "data" folder, change these to "data/filename.feather"
IBES_PATH = "ibes_dj30_stock_rec_2008_24.feather"
FUND_PATH = "fund_tech_dj30_stocks_2008_24.feather"
NEWS_PATH = "ciq_dj30_stock_news_2008_24.feather"


def inspect_df(name, df, show_rows=5):
    print(f"\n===== {name} =====")
    print(f"Shape: {df.shape}")  # (rows, columns)
    print("\nColumns:")
    print(list(df.columns))

    print("\nDtypes:")
    print(df.dtypes)

    print(f"\nFirst {show_rows} rows:")
    # to_string() so the printout is clean in the terminal
    print(df.head(show_rows).to_string(index=False))
    print("=" * 40)


def main():
    # Load each feather file
    ibes = pd.read_feather(IBES_PATH)
    fund = pd.read_feather(FUND_PATH)
    news = pd.read_feather(NEWS_PATH)

    inspect_df("IBES", ibes)
    inspect_df("FUND", fund, show_rows=3)
    inspect_df("NEWS", news, show_rows=5)


if __name__ == "__main__":
    main()
