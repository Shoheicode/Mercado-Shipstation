import pdfplumber
import re
from pathlib import Path

def get_order_number_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        all_text = []

        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_text.append(text)

    text = "\n".join(all_text)

    with open("output1.txt", "w", encoding="utf-8") as f:
        print("Writing text to output1.txt...")
        f.write(text)

def read_txt_and_extract_order_number():
    txt_path = Path("output1.txt")

    text = txt_path.read_text(encoding="utf-8", errors="ignore")

    match = re.search(r"(?:Pack\s*ID\s*:|US\s*Order\s*#)\s*(\d+)", text, re.IGNORECASE)

    if match:
        order_number = match.group(1)
        print("Order number:", order_number)
        return order_number
    else:
        print("Order number not found")

def main():
    pdf_path = Path("Binder1.pdf")
    get_order_number_from_pdf(pdf_path)
    read_txt_and_extract_order_number()

if __name__ == "__main__":
    main()