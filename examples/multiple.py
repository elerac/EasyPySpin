"""Example of capture with multiple camera.
"""
import EasyPySpin
import cv2


def main():
    # cap = EasyPySpin.MultipleVideoCapture(0)
    cap = EasyPySpin.MultipleVideoCapture(0, 1)
    # cap = EasyPySpin.MultipleVideoCapture(0, 1, 2)

    if not all(cap.isOpened()):
        print("All cameras can't open\nexit")
        return -1

    while True:
        read_values = cap.read()

        for i, (ret, frame) in enumerate(read_values):
            if not ret:
                continue

            frame = cv2.resize(frame, None, fx=0.25, fy=0.25)
            cv2.imshow(f"frame-{i}", frame)

        key = cv2.waitKey(30)
        if key == ord("q"):
            break

    cv2.destroyAllWindows()
    cap.release()


if __name__ == "__main__":
    main()
