import fitz
from PIL import Image
import os
import tempfile
import sys

pdf_path = "sample.pdf"
doc = fitz.open(pdf_path)
current_page = 0
current_temp_file = None

def render_page(page_number):
    global current_temp_file
    if current_temp_file and os.path.exists(current_temp_file):
        os.remove(current_temp_file)
    
    page = doc[page_number]
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    image.save(temp_file.name)
    current_temp_file = temp_file.name

    os.system(f"open {current_temp_file}")

render_page(current_page)

for line in sys.stdin:
    cmd = line.strip()
    if cmd.upper() == 'Q':
        break
    elif cmd.upper() == 'N':
        if current_page < len(doc) - 1:
            current_page += 1
    elif cmd.upper() == 'P':
        if current_page > 0:
            current_page -= 1
    elif cmd.isdigit():
        page = int(cmd) - 1
        if 0 <= page < len(doc):
            current_page = page

    render_page(current_page)
    print(current_page + 1, flush=True)  # 回傳目前頁數給主程式

doc.close()
if current_temp_file and os.path.exists(current_temp_file):
    os.remove(current_temp_file)
