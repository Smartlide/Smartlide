import sounddevice as sd
import numpy as np
import queue
import threading
from faster_whisper import WhisperModel
from opencc import OpenCC

MODEL_SIZE = "small"
SAMPLE_RATE = 16000
CHUNK_DURATION = 3
SILENCE_THRESHOLD = 0.01
LANGUAGE = "zh"

class SpeechRecognizer:
    def __init__(self, text_queue):
        self.model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
        self.converter = OpenCC('s2t')
        self.audio_queue = queue.Queue()
        self.text_queue = text_queue
        self.running = False

    def is_speech(self, audio_block):
        rms = np.sqrt(np.mean(audio_block ** 2))
        return rms > SILENCE_THRESHOLD

    def audio_callback(self, indata, frames, time_info, status):
        if status:
            print("錄音狀態異常:", status)
        if self.is_speech(indata):
            self.audio_queue.put(indata.copy())

    def process_audio(self):
        while self.running:
            audio_block = self.audio_queue.get()
            audio_block = audio_block.flatten()
            try:
                segments, _ = self.model.transcribe(audio_block, language=LANGUAGE)
                combined_text = "".join([s.text.strip() for s in segments])
                combined_text = self.converter.convert(combined_text.strip())

                if combined_text:
                    # 寫入 output.txt
                    with open("output.txt", "a", encoding="utf-8") as f:
                        f.write(combined_text)

                    # 傳入文字佇列給 Ollama 模組
                    if self.text_queue.full():
                        self.text_queue.get()
                    self.text_queue.put(combined_text)

            except Exception as e:
                print(f"語音辨識錯誤: {e}")

    def start(self):
        self.running = True
        threading.Thread(target=self.process_audio, daemon=True).start()

        # 清空舊的 output.txt
        with open("output.txt", "w", encoding="utf-8") as f:
            f.write("")

        print("開始錄音中... (Ctrl+C 結束)")
        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype='float32',
                blocksize=int(SAMPLE_RATE * CHUNK_DURATION),
                callback=self.audio_callback
            ):
                while self.running:
                    sd.sleep(1000)
        except KeyboardInterrupt:
            self.running = False
            print("錄音結束。")