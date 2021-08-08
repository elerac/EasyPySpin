"""Example of synchronized capture with multiple cameras.

You need to create a physical connection between the cameras by linking their GPIO pins, as follows:
https://www.flir.com/support-center/iis/machine-vision/application-note/configuring-synchronized-capture-with-multiple-cameras/
"""
import EasyPySpin
import cv2


def main():
    serial_number_1 = "20541712"  # primary camera (set your camera's serial number)
    serial_number_2 = "19412150"  # secondary camera (set your camera's serial number)
    cap = EasyPySpin.SynchronizedVideoCapture(serial_number_1, serial_number_2)

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
