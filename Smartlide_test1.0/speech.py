import whisper
import pyaudio
import numpy as np

# 載入 Whisper 模型
model = whisper.load_model("small")

# 音訊參數
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 5

# 初始化 PyAudio
p = pyaudio.PyAudio()

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

print("開始錄音（按 Ctrl+C 停止）")

# 🔹 變數設定
current_text = ""  # 儲存這一次辨識的文字
all_text = ""      # 累積所有辨識的文字

try:
    with open("output.txt", "a", encoding="utf-8") as file:  # 以附加模式開啟
        while True:
            frames = []
            for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(np.frombuffer(data, dtype=np.int16))

            audio_np = np.concatenate(frames, axis=0).astype(np.float32) / 32768.0
            result = model.transcribe(audio_np)

            # 存入當前辨識結果
            current_text = result["text"]
            all_text += current_text + " "  # 累加到總辨識結果

            print("當前辨識結果:", current_text)

            # 寫入文字檔
            file.write(current_text + "\n")
            file.flush()  # 立即寫入磁碟，防止程式異常時資料丟失

except KeyboardInterrupt:
    print("\n停止錄音")
    print("\n最終轉錄內容：", all_text)  # 顯示完整結果
    stream.stop_stream()
    stream.close()
    p.terminate()
