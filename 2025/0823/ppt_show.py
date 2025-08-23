import fitz
from PIL import Image, ImageDraw
import os
import tempfile
import sys
import subprocess
import difflib

pdf_path = "final.pdf"
doc = fitz.open(pdf_path)
current_page = 0
current_temp_file = None
page_annotations = {}  # 記錄每次的畫底線動作
page_highlights = {}  # 記錄每次的畫螢光筆動作

def render_page(page_number):
    global current_temp_file
    if current_temp_file and os.path.exists(current_temp_file):
        os.remove(current_temp_file)

    page = doc[page_number]
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 放大兩倍，座標用兩倍處理
    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples).convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")

    scale = 2.0
    text_dict = page.get_text("dict")

    annotations = page_annotations.get(page_number, [])
    for highlight_text in annotations:
        # 用 search_for 找出所有完全符合的文字區域
        rects = page.search_for(highlight_text)

        # 先對應有沒有完全符合的文字
        if rects:
            for rect in rects:
                x0 = rect.x0 * scale
                x1 = rect.x1 * scale
                y1 = rect.y1 * scale
                underline_y = int(y1 + 5)
                draw.line((x0, underline_y, x1, underline_y), fill="red", width=3)

        else:
            # 若沒有完全符合再找最相近的片段
            best_match = None
            highest_ratio = 0
            best_span_rect = None
            for block in text_dict["blocks"]:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        span_text = span["text"]
                        ratio = difflib.SequenceMatcher(None, highlight_text, span_text).ratio()
                        if ratio > highest_ratio:
                            highest_ratio = ratio
                            best_match = span_text
                            # 只取該片段的範圍
                            x0 = span["bbox"][0] * scale
                            x1 = span["bbox"][2] * scale
                            y1 = span["bbox"][3] * scale
                            best_span_rect = (x0, x1, y1)
            
            # 只在相似度高於 0.2 時畫底線
            if best_span_rect and highest_ratio > 0.2:
                # 使用最佳匹配的範圍，畫底線
                underline_y = int(best_span_rect[2] + 5)  # 在文字下方畫底線
                draw.line((best_span_rect[0], underline_y, best_span_rect[1], underline_y), fill="orange", width=3)
                print(f"找不到完全符合，已針對最相近片段「{best_match}」畫底線（相似度：{highest_ratio:.2f}）")
            else:
                print(f"找不到「{highlight_text}」在本頁（完全符合與相似度都不足）")

    highlights = page_highlights.get(page_number, [])
    for highlight_text in highlights:
        rects = page.search_for(highlight_text)
        if rects:
            for rect in rects:
                x0 = rect.x0 * scale
                y0 = rect.y0 * scale
                x1 = rect.x1 * scale
                y1 = rect.y1 * scale
                # 建立一個半透明黃色的圖層
                highlight_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
                highlight_draw = ImageDraw.Draw(highlight_layer)
                highlight_draw.rectangle([x0, y0, x1, y1], fill=(255, 255, 0, 80))  # 80~120都很適合
                image = Image.alpha_composite(image, highlight_layer)
                
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    image.save(temp_file.name)
    current_temp_file = temp_file.name
    subprocess.Popen(["open", current_temp_file])  # mac開圖片(和winows、linux 不一樣)


render_page(current_page)

################################################################################################################################################################################################

# 指令動作
for line in sys.stdin:
    cmd = line.strip()
    update = False

    # 結束指令
    if cmd.upper() == 'Q':
        break

    # 下一頁(N)
    elif cmd.upper() == 'N':
        if current_page < len(doc) - 1:
            current_page += 1
            update = True

    # 上一頁(P)
    elif cmd.upper() == 'P':
        if current_page > 0:
            current_page -= 1
            update = True

    # 畫底線(U:文字內容)
    elif cmd.upper().startswith("U:"):
        highlight_text = cmd[2:].strip()
        if highlight_text:
            page_annotations.setdefault(current_page, []).append(highlight_text)
        update = True
    elif cmd.upper() == 'U':
        update = True

    # 畫螢光筆(H:文字內容)
    elif cmd.upper().startswith("H:"):
        highlight_text = cmd[2:].strip()
        if highlight_text:
            page_highlights.setdefault(current_page, []).append(highlight_text)
        update = True
    elif cmd.upper() == 'H':
        update = True

    # 翻到指定頁面（數字）
    elif cmd.isdigit():
        page = int(cmd) - 1
        if 0 <= page < len(doc):
            current_page = page
            update = True

    if update:
        render_page(current_page)
        print(current_page + 1, flush=True)

doc.close()
if current_temp_file and os.path.exists(current_temp_file):
    os.remove(current_temp_file)
