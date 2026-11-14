import threading
import cv2 as cv

class VideoStream:
    def __init__(self, source: int | str = 0):
        self.stream = cv.VideoCapture(source)
        self.connected, self.latest_frame = self.stream.read()
        self.running = True

        self.worker = threading.Thread(target=self.update, daemon= True)
        self.worker.start()

    def update(self):
        while self.running:
            self.connected, self.latest_frame = self.stream.read()

            if not self.connected:
                self.running = False
                break

    def read(self):
        return self.connected, self.latest_frame.copy()

    def stop(self):
        self.running = False
        self.worker.join()
        self.stream.release()

