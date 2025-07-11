import queue
import threading
import speech_recognition as sr
import time
import subprocess
from collections import deque

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
            # print("請開始說話...")
            audio = recognizer.listen(source)
        audio_queue.put(audio)

def call_script(text):
    try:
        process = subprocess.Popen(
            ["python3", "text_judge.py", text],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        if stderr:
            print(f"text_judge.py 錯誤: {stderr.decode().strip()}")
        return stdout.decode().strip()
    except Exception as e:
        print(f"呼叫 text_judge.py 時發生錯誤: {e}")
        return None

def transcribe_audio():
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
                response = call_script(text)

                # 傳送動作到 PDF 控制器
                if response:
                    pdf_process.stdin.write(response + "\n")
                    pdf_process.stdin.flush()

                    # 嘗試接收目前頁數
                    try:
                        returned_page = pdf_process.stdout.readline().strip()
                        if returned_page.isdigit():
                            current_page = int(returned_page)
                    except:
                        pass

                # 輸出格式化資訊
                print("\n語音轉錄：", text)
                print("累積語音：", " ".join(text_queue))
                print("判斷動作：", response)
                print("目前頁數：", current_page)

                with open("output.txt", "a", encoding="utf-8") as f:
                    f.write(text + "\n")

                if response and response != 'S':
                    print("清空queue內容，重新開始")
                    text_queue.clear()

recording_thread = threading.Thread(target=record_audio, daemon=True)
transcribing_thread = threading.Thread(target=transcribe_audio, daemon=True)

recording_thread.start()
transcribing_thread.start()

while True:
    time.sleep(0.1)