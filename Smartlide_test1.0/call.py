import ollama

#=============================================================================================
selected_model = "llama3.1"
# ollama serve &
# ollama run llama3.1

#=============================================================================================

def predict_slide_action(text):
    prompt = (
        "你現在是一個簡報輔助系統，目的是幫助演講者判斷是否需要翻頁。請遵循以下規則：\n"
        "1. 你需要分析輸入的話語，並判斷是否有翻頁需求。\n"
        "2. 你必須計算「要翻頁的機率」和「不用翻頁的機率」，兩者相加必須等於 1。\n"
        "3. 當「要翻頁的機率」≥ 90% 時，你應該輸出 'N'，表示需要翻頁。\n"
        "4. 當「要翻頁的機率」< 90% 時，你應該輸出 'S'，表示不需要翻頁。\n"
        "5. 你的輸出必須嚴格只包含 數字、'N' 或 'S'，不可以有其他額外內容。\n"
        "6. 請不要因為句子中含有『下』這種有『往後』含義的字眼，而導致你預測翻頁的機率過度提高，請你判斷前後文。\n"
        "7. 若輸入為『第n頁』的相似語句，請你輸出此n的數字。\n"
        "你可以依據以下語境來判斷機率：\n"
        "(1) 高翻頁機率（99% 以上）：話語包含『下一頁』、『下一張簡報』等。\n"
        "(2) 低翻頁機率（10% 以下）：話語包含『讓我們再看一下』、『這邊補充一下』、『這部分再說明一下』、『下課』、『下堂課』、『下一句』、『下述』等。\n"
        "請分析以下話語，並『切記』你只能回應我只能一個字，『我不要』除了輸字、'N' 、'S'以外的輸出。\n"
    )

    text = f"{text}\n"
    
    # 呼叫 ollama.chat 並傳入 prompt 和用戶的訊息
    response = ollama.chat(
        model='llama3.1',
        messages=[
            {'role': 'system', 'content': prompt},
            {'role': 'user', 'content': text}  # 用戶輸入的句子
        ]
    )

    # 輸出整個 response 來檢查它的結構
    #print("Response:", response)
    
    # 從 response 中獲取模型的輸出
    output = ''
    if 'message' in response:
        output = response['message'].get('content', '').strip()
    return output

#=============================================================================================

# 主程式，從終端接收輸入
if __name__ == "__main__":

    # 請提供要讀取的檔案名稱
    file_path = "input_text.txt"  # 這是文字檔的名稱或路徑，請根據實際情況修改
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                text_input = line.strip()  # 去除首尾空格
                if text_input:  # 避免處理空行
                    result = predict_slide_action(text_input)
                    print("輸出 : ",result)
    except FileNotFoundError:
        print(f"檔案 {file_path} 未找到，請確認檔案路徑是否正確。")