import cv2 as cv
import stream
import tracker


def main():
    source = "rtsp://camera:8554/cam"
    vstream = stream.VideoStream(source=source)
    ptracker = tracker.Tracker()

    try:
        while True:
            connected, frame = vstream.read()

            if not connected or frame is None:
                print("no more stream")
                break

            tracking_res = ptracker.track(frame)

            print([p.id for p in tracking_res])

            cv.imshow("test_stream", frame)
            if cv.waitKey(1) == ord('q'):
                break

    except KeyboardInterrupt:
        print("\nStopping stream...")
    finally:
        vstream.stop()
        cv.destroyAllWindows()


if __name__ == "__main__":
    main()
