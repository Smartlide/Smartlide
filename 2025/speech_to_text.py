import queue
import threading
import speech_recognition as sr
import time
import subprocess
from collections import deque
import asyncio

MAX_QUEUE_SIZE = 5
audio_queue = queue.Queue()
text_queue = deque(maxlen=MAX_QUEUE_SIZE)
current_page = 1

def record_audio():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    print("開始錄音...")

    while True:
        with mic as source:
            audio = recognizer.listen(source)
        audio_queue.put(audio)

async def call_script(text):
    try:
        process = subprocess.Popen(
            ["python3", "text_judge.py", text],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        if stderr:
            print(f"text_judge.py 錯誤: {stderr.decode().strip()}")
        return stdout.strip()
    except Exception as e:
        print(f"呼叫 text_judge.py 時發生錯誤: {e}")
        return None

async def transcribe_audio():
    global current_page
    recognizer = sr.Recognizer()
    pdf_process = subprocess.Popen(
        ["python3", "ppt_show.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    while True:
        if not audio_queue.empty():
            while audio_queue.qsize() > 1:
                audio_queue.get()
            audio = audio_queue.get()
            try:
                text = recognizer.recognize_google(audio, language="zh-TW").strip()
            except sr.UnknownValueError:
                text = ""
                print("無法辨識語音")
            except sr.RequestError as e:
                text = ""
                print(f"語音辨識服務錯誤: {e}")

            if text:
                text_queue.append(text)
                response = await call_script(text)

                if response:
                    # 內文化底線(U:)
                    if response.startswith("U:"):
                        pdf_process.stdin.write(response + "\n")
                        pdf_process.stdin.flush()

                    # 內文畫螢光筆(H:)
                    elif response.startswith("H:"):
                        pdf_process.stdin.write(response + "\n")
                        pdf_process.stdin.flush()

                    # 更換頁面（數字、N、P）
                    elif response != "S":
                        pdf_process.stdin.write(response + "\n")
                        pdf_process.stdin.flush()

                        # 接收回傳的目前頁碼
                        try:
                            returned_page = pdf_process.stdout.readline().strip()
                            if returned_page.isdigit():
                                current_page = int(returned_page)
                        except Exception as e:
                            print(f"讀取頁碼錯誤：{e}")

                # 輸出格式化資訊
                print("\n語音轉錄：", text)
                print("累積語音：", " ".join(text_queue))
                print("判斷動作：", response)
                print("目前頁數：", current_page)

                with open("output.txt", "a", encoding="utf-8") as f:
                    f.write(text)

                if response and response != 'S':
                    print("清空queue內容，重新開始")
                    text_queue.clear()

# 重新設計錄音與轉錄流程為協同工作
async def main():
    recording_thread = threading.Thread(target=record_audio, daemon=True)
    recording_thread.start()

    # 使用 asyncio 來運行轉錄過程
    await transcribe_audio()

# 啟動主程式
if __name__ == "__main__":
    with open("output.txt", "w", encoding="utf-8") as f:
        pass
    asyncio.run(main())
