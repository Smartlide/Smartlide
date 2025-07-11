import ollama
import re
import sys

selected_model = "llama3.1"

def predict_slide_action(text):
    prompt = (
        "你是簡報輔助系統，目的是判斷是否需要翻頁。請遵守以下規則：\n"
        "1. 分析輸入的話語，判斷是否需要翻頁。\n"
        "2. 計算「要翻頁的機率」和「不用翻頁的機率」，兩者總和必須為 1。\n"
        "3. 當「要翻頁的機率」>= 80% 時，輸出 'N'，表示需要往後翻頁（下一頁）。\n"
        "4. 當「要翻頁的機率」< 80% 時，輸出 'S'，表示不需要翻頁。\n"
        "5. 當語句明確表示『往前翻一頁』、『上一頁』、『回到上一頁』等，請輸出 'P'。\n"
        "6. 當語句明確指出『第X頁』、『第X張』、『跳到第X頁』，不論X是中文數字還是阿拉伯數字，都請輸出該頁數（阿拉伯數字）。\n"
        "7. 輸出僅限數字、'N'、'P' 或 'S'，不得有其他內容。\n"
        "8. 不要因為「下」這類有『往後』含義的字眼過度預測翻頁，需根據上下文判斷。\n"
        "9. 只有在明確提到頁數時才輸出數字。\n"
        "語境判斷指引：\n"
        "- 高翻頁機率（99% 以上）：包含「下一頁」、「下一張簡報」等。\n"
        "- 前一頁指令：包含「上一頁」、「往前翻一頁」、「回到上一頁」等。\n"
        "- 低翻頁機率（10% 以下）：包含「讓我們再看一下」、「這邊補充一下」、「下課」等。\n"
        "請分析以下話語，並「記得」僅回應數字、'N'、'P' 或 'S'，只有在明確提到頁數時才輸出數字。"
    )

    text = f"{text}\n"

    # 處理中文數字轉阿拉伯數字
    def chinese_to_arabic(cn):
        cn_num = {
            '零': 0, '一': 1, '二': 2, '兩': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10
        }
        if cn.isdigit():
            return int(cn)
        if cn in cn_num:
            return cn_num[cn]
        # 支援「十一」、「二十五」這種複合數字
        if '十' in cn:
            parts = cn.split('十')
            if parts[0] == '':
                left = 1
            else:
                left = cn_num.get(parts[0], 0)
            if len(parts) == 1 or parts[1] == '':
                right = 0
            else:
                right = cn_num.get(parts[1], 0)
            return left * 10 + right
        return None

    while True:
        response = ollama.chat(
            model=selected_model,
            messages=[
                {'role': 'system', 'content': prompt},
                {'role': 'user', 'content': text}
            ]
        )

        output = ''
        if 'message' in response:
            output = response['message'].get('content', '').strip()

        # 先判斷是否為上一頁指令
        if output.lower() == 'p':
            return 'P'
        # 判斷是否為下一頁或不翻頁
        elif output.lower() in ['n', 's']:
            return output.upper()
        # 判斷是否為阿拉伯數字
        elif re.match(r'^\d+$', output):
            return output
        # 判斷是否為中文數字
        elif re.match(r'^[零一二兩三四五六七八九十]+$', output):
            arabic = chinese_to_arabic(output)
            if arabic is not None:
                return str(arabic)
        else:
            continue  # 無效則重新執行預測

# 主程式，從命令列接收輸入
if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_text = sys.argv[1]
        result = predict_slide_action(input_text)
        print(result)
    else:
        print("未接收到輸入文字")
