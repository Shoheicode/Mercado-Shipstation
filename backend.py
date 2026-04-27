import os

import pandas as pd
import pdfplumber
import re
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from MercadoLibre import MercadoLibreClient

CLIENT_ID = os.environ.get("ML_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("ML_CLIENT_SECRET", "").strip()
REDIRECT_URI = os.environ.get("ML_REDIRECT_URI", "").strip()
AUTH_CODE = os.environ.get("ML_AUTH_CODE", "").strip()

PDF_FOLDER = Path("uploads_pdf")  # change this to your folder path
OUTPUT_CSV = "extracted_orders.csv"

def get_order_number_from_pdf(pdf_path, text_file_name="output1.txt"):
    with pdfplumber.open(pdf_path) as pdf:
        all_text = []

        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_text.append(text)

    text = "\n".join(all_text)

    with open(text_file_name, "w", encoding="utf-8") as f:
        print(f"Writing text to {text_file_name}...")
        f.write(text)

def read_txt_and_extract_order_number(text_file_name="output1.txt"):
    txt_path = Path(text_file_name)

    text = txt_path.read_text(encoding="utf-8", errors="ignore")

    match = re.search(r"(?:Pack\s*ID\s*:|US\s*Order\s*#)\s*(\d+)", text, re.IGNORECASE)

    if match:
        order_number = match.group(1)
        print("Order number:", order_number)
        return order_number
    else:
        print("Order number not found")

def running_backend():

    ml_api = MercadoLibreClient(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        auth_code=AUTH_CODE,
    )

    results = []

    for pdf_path in PDF_FOLDER.glob("*.pdf"):
        try:
            print(f"Processing {pdf_path}...")
            text_file_name = f"{pdf_path.stem}_output.txt"
            get_order_number_from_pdf(pdf_path, text_file_name)
            order = read_txt_and_extract_order_number(text_file_name)
            print(f"Processed {pdf_path.name}: Order Number - {order if order else 'NOT FOUND'}")

            if order:
                results.append({
                    "file_name": pdf_path.name,
                    "order_number": order
                })
            else:
                results.append({
                    "file_name": pdf_path.name,
                    "order_number": "NOT FOUND"
                })
        except Exception as e:
            print(f"Error processing {pdf_path}: {e}")
            continue

    df = pd.DataFrame(results)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Results saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    running_backend()