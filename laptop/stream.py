import cv2 as cv

stream = cv.VideoCapture(0)

if not stream.isOpened():
    print("No stream :(")
    exit()

while(True):
    ret, frame = stream.read()

    if not ret:
        print("No more stream :(")
        break

    cv.imshow("Webcam", frame)

    if cv.waitKey(1) == ord('q'):
        break

stream.release()
cv.destroyAllWindows()

