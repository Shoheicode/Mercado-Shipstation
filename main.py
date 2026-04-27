import pdfplumber
import pandas as pd

tables = []

with pdfplumber.open("input.pdf") as pdf:
    for page_number, page in enumerate(pdf.pages, start=1):
        page_tables = page.extract_tables()

        for table in page_tables:
            df = pd.DataFrame(table)
            df["source_page"] = page_number
            tables.append(df)

if tables:
    final_df = pd.concat(tables, ignore_index=True)
    final_df.to_csv("tables.csv", index=False)