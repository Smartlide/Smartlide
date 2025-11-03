import fitz
import difflib
from PIL import Image
import tempfile, subprocess, os

class PDFController:
    def __init__(self, pdf_path):
        self.doc = fitz.open(pdf_path)
        self.current_page = 0
        self.temp_file = None

    def render(self):
        if self.temp_file and os.path.exists(self.temp_file):
            os.remove(self.temp_file)
        page = self.doc[self.current_page]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        img.save(temp.name)
        self.temp_file = temp.name
        subprocess.Popen(["open", self.temp_file])

    def fuzzy_search(self, page, text):
        text_dict = page.get_text("dict")
        best_match, best_ratio, best_rect = None, 0, None
        for block in text_dict["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    ratio = difflib.SequenceMatcher(None, text, span["text"]).ratio()
                    if ratio > best_ratio:
                        best_match, best_ratio, best_rect = span["text"], ratio, fitz.Rect(span["bbox"])
        return best_rect if best_ratio > 0.2 else None

    def handle_command(self, cmd):
        page = self.doc[self.current_page]
        update = False

        if cmd == 'N' and self.current_page < len(self.doc) - 1:
            self.current_page += 1; update = True
        elif cmd == 'P' and self.current_page > 0:
            self.current_page -= 1; update = True
        elif cmd.isdigit():
            p = int(cmd) - 1
            if 0 <= p < len(self.doc): self.current_page = p; update = True
        elif cmd.startswith("U:"):
            text = cmd[2:].strip()
            rects = page.search_for(text) or []
            if not rects:
                rect = self.fuzzy_search(page, text)
                if rect: rects = [rect]
            if rects:
                page.add_underline_annot(rects).update(); update = True
        elif cmd.startswith("H:"):
            text = cmd[2:].strip()
            rects = page.search_for(text) or []
            if rects:
                page.add_highlight_annot(rects).update(); update = True

        if update:
            self.render()
            print(f"顯示第 {self.current_page + 1} 頁")

    def save_and_close(self):
        output = "output_annotated.pdf"
        self.doc.save(output, garbage=3)
        print(f"已儲存 {output}")
        self.doc.close()
        if self.temp_file and os.path.exists(self.temp_file):
            os.remove(self.temp_file)
