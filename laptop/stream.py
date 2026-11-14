import cv2 as cv


if not stream.isOpened():
    print("No stream :(")
    exit()

while(True):
    ret, frame = stream.read()

    if not ret:
        print("No more stream :(")
        break

    cv.imshow("Webcam", frame)

    if cv.waitKey(1) == ord ('q'):
        break

stream.release()
cv.destroyAllWindows()

class VideoStream:

    def __init__(self, frame):
        self.stream = cv.VideoCapture(0)
        self.latest_frame = frame