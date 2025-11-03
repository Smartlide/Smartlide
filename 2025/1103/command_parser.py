import ollama
import re

selected_model = "llama3.1"

class CommandParser:
    def __init__(self):
        self.model = selected_model

    # ==============================
    # 清除標記文字中的關鍵詞
    # ==============================
    def clean_mark_text(self, text):
        keywords = [
            "畫底線", "底線", "underline",
            "畫重點", "標記重點",
            "畫螢光筆", "螢光筆", "highlight"
        ]
        text = text.strip()
        for kw in keywords:
            if text.lower().startswith(kw):
                text = text[len(kw):].strip()
            elif text.lower().endswith(kw):
                text = text[:-len(kw)].strip()
        return text

    # ==============================
    # 中文數字轉換
    # ==============================
    def chinese_to_arabic(self, cn):
        cn_num = {
            '零': 0, '一': 1, '二': 2, '兩': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10
        }
        if cn.isdigit():
            return int(cn)
        if cn in cn_num:
            return cn_num[cn]
        if '十' in cn:
            parts = cn.split('十')
            left = cn_num.get(parts[0], 1 if parts[0] == '' else 0)
            right = cn_num.get(parts[1], 0 if len(parts) == 1 or parts[1] == '' else cn_num[parts[1]])
            return left * 10 + right
        return None

    # ==============================
    # 語意判斷（主功能）
    # ==============================
    def predict_action(self, text):
        # 預處理：容錯 "under line" / "high light" 等錯字
        text = text.lower().replace("under line", "underline").replace("high light", "highlight")
        text = text.replace("highlighted", "highlight")

        # 給 Ollama 的 prompt
        prompt = (
            "你是簡報輔助系統，請根據使用者的語句判斷是否為操作指令。\n"
            "請嚴格遵守以下規則：\n"
            "1. 若語句只是講述內容（朗讀、解釋），請輸出 'S'。\n"
            "2. 若語句提到「下一頁」「往後」「next page」「continue」等，輸出 'N'。\n"
            "3. 若語句提到「上一頁」「回去」「previous page」「go back」等，輸出 'P'。\n"
            "4. 若語句包含「第X頁」「page X」「go to page X」等，輸出數字 X。\n"
            "5. 若語句包含 'underline' 或 中文的「畫底線」「底線」「畫重點」「標記重點」 → 輸出 'U'。\n"
            "6. 若語句包含 'highlight' 或 中文的「畫螢光筆」「螢光筆」 → 輸出 'H'。\n"
            "7. 若模糊或無法確定，輸出 'S'。\n"
            "輸出只能是以下其中之一：'N'、'P'、'S'、'U'、'H' 或 數字。禁止輸出其他內容。"
        )

        # 呼叫 Ollama 模型
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': prompt},
                    {'role': 'user', 'content': text}
                ]
            )
            output = response.get('message', {}).get('content', '').strip()
        except Exception as e:
            print(f"Ollama error: {e}")
            return "S"

        # ==============================
        # 後處理：決定最終指令格式
        # ==============================
        if output.lower() == 'u' or 'underline' in text or any(k in text for k in ['畫底線', '底線']):
            clean_text = self.clean_mark_text(text)
            return f"U:{clean_text}"
        elif output.lower() == 'h' or 'highlight' in text or any(k in text for k in ['螢光筆']):
            clean_text = self.clean_mark_text(text)
            return f"H:{clean_text}"
        elif output.lower() in ['n', 'p', 's']:
            return output.upper()
        elif re.match(r'^\d+$', output):
            return output
        elif re.match(r'^[零一二兩三四五六七八九十]+$', output):
            arabic = self.chinese_to_arabic(output)
            if arabic is not None:
                return str(arabic)
        return "S"
