from pypdf import PdfReader

reader = PdfReader("Binder1.pdf")

all_text = []

for page in reader.pages:
    text = page.extract_text()
    if text:
        all_text.append(text)

result = "\n".join(all_text)

with open("output.txt", "w", encoding="utf-8") as f:
    f.write(result)