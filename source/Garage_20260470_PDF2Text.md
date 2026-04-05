## Extract Text from PDF via PDFplumber

A command-line Python script that opens a PDF file, extracts all textual content page-by-page using **PDFplumber**, and writes the result as a UTF-8 encoded plain-text (`.txt`) file. 

**Usage Instructions**     

You can also test the script using [**our standalone Python Notebook (HTML)**](Garage_20260405_ipynb.html).

**Prerequisites**     
- Python 3.x installed and reachable on the system `PATH`.
- No manual package installation is required — the script installs `pdfplumber` automatically on first run if it is absent.
- A UTF-8 encoded `.pdf` file.

**Running the Script**

```bash
python pdf2text_via_PDFplumber.py <path_to_pdf_file>
```

`<path_to_pdf_file>` must be the path (absolute or relative to CWD) of an existing file whose name ends in `.pdf` (case-insensitive). The output `.txt` is always written to the **current working directory**, not the directory of the input file.

**Code (with inline comments)**

```python
import subprocess
import sys
import os
#
def install_package(package):
    """Silently install a package if not already installed"""
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q"])
# Check and install required packages
required_packages = {
    'pdfplumber': 'pdfplumber'
}
for import_name, package_name in required_packages.items():
    try:
        __import__(import_name)
    except ImportError:
        print(f"Installing {package_name}...")
        install_package(package_name)  
import pdfplumber
# Check if file path is provided as command-line argument
if len(sys.argv) < 2:
    print("Usage: python pdf2text_via_PDFplumber.py <path_to_pdf_file>")
    sys.exit(1)
# Get file path from command-line argument
file_path = sys.argv[1]
# Check if file exists
if not os.path.exists(file_path):
    print(f"Error: File '{file_path}' not found.")
    sys.exit(1)
# Check if file is a PDF
if not file_path.lower().endswith('.pdf'):
    print("Error: File must be a PDF.")
    sys.exit(1)
# Extract PDF text
print(f"Extracting text from '{file_path}'...")
text = ""
try:
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted is not None:
                text += extracted + " "
except Exception as e:
    print(f"Error extracting text from PDF: {e}")
    sys.exit(1)
# Print text length to verify extraction
print(f"Extracted text length: {len(text)} characters")
# Generate output filename based on input filename
output_file = os.path.splitext(os.path.basename(file_path))[0] + ".txt"
# Save extracted text to .txt file
try:
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Text saved as '{output_file}'")
except Exception as e:
    print(f"Error saving text file: {e}")
    sys.exit(1)
```