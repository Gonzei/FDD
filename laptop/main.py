import time
import cv2 as cv
import stream


def main():
    source = "rtsp://camera:8554/cam"
    vstream = stream.VideoStream(source=source)

    try:
        while True:
            connected, frame = vstream.read()

            if not connected or frame is None:
                print("no more stream")
                break

            # --- Headless Container Preview ---
            cv.imwrite("live.jpg", frame)
            time.sleep(0.05)

            # --- Local GUI Preview ---
            # cv.imshow("test_stream", frame)
            # if cv.waitKey(1) == ord('q'):
            #     break

    except KeyboardInterrupt:
        print("\nStopping stream...")
    finally:
        vstream.stop()
        # cv.destroyAllWindows()


if __name__ == "__main__":
    main()
