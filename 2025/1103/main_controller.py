import queue
import threading
import time
from speech_recognition import SpeechRecognizer  # 你的語音模組
from command_parser import CommandParser
from pdf_controller import PDFController

MAX_QUEUE_SIZE = 3

def main():
    # ===== 初始化模組 =====
    text_queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)
    recognizer = SpeechRecognizer(text_queue)  # 假設會自動把文字放到 queue
    parser = CommandParser()
    pdf = PDFController("week0.pdf")
    pdf.render()  # 初始渲染 PDF

    # ===== 自動管理 queue，保持最新三條 =====
    def add_to_queue(text):
        while text_queue.qsize() >= MAX_QUEUE_SIZE:
            try:
                text_queue.get_nowait()  # 刪掉最舊的
            except queue.Empty:
                break
        text_queue.put_nowait(text)

    # ===== 指令處理執行緒 =====
    def command_worker():
        while True:
            if not text_queue.empty():
                # 合併 queue 內容成完整語句
                text = "".join(list(text_queue.queue))
                print(f"\n語音辨識結果：{text}")

                # 語意判斷
                cmd = parser.predict_action(text)
                if cmd != "S":
                    print(f"指令：{cmd}")
                    pdf.handle_command(cmd)

                # 無論是否有操作指令，都清空 queue
                with text_queue.mutex:
                    text_queue.queue.clear()
            time.sleep(0.1)  # 避免 CPU 過高

    # ===== 啟動指令處理執行緒 =====
    threading.Thread(target=command_worker, daemon=True).start()

    # ===== 啟動語音辨識 =====
    try:
        # 假設 recognizer.start() 會持續辨識語音並把文字放入 queue
        recognizer.start()  
    except KeyboardInterrupt:
        print("\n結束簡報控制")
        pdf.save_and_close()

if __name__ == "__main__":
    main()
