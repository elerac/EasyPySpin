"""
Command line accessible tool
"""
from .videocapture import VideoCapture
import cv2
import argparse


def print_xy(event, x, y, flags, param):
    """
    Export xy coordinates in csv format by clicking
    """
    if event == cv2.EVENT_LBUTTONDOWN:
        scale = param
        print(f"{int(x/scale)}, {int(y/scale)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--index",      type=int,   default=0,   help="Camera index (Default: 0)")
    parser.add_argument("-e", "--exposure",   type=float, default=-1,  help="Exposure time [us] (Default: Auto)")
    parser.add_argument("-g", "--gain",       type=float, default=-1,  help="Gain [dB] (Default: Auto)")
    parser.add_argument("-G", "--gamma",      type=float,              help="Gamma value")
    parser.add_argument("-b", "--brightness", type=float,              help="Brightness [EV]")
    parser.add_argument("-f", "--fps",        type=float,              help="FrameRate [fps]")
    parser.add_argument("-s", "--scale",      type=float, default=.25, help="Image scale to show (>0) (Default: 0.25)")
    args = parser.parse_args()

    # Instance creation
    cap = VideoCapture(args.index)

    # Checking if it's connected to the camera
    if not cap.isOpened():
        print("Camera can't open\nexit")
        return -1

    # Set the camera parameters
    cap.set(cv2.CAP_PROP_EXPOSURE, args.exposure)  # -1 sets exposure_time to auto
    cap.set(cv2.CAP_PROP_GAIN, args.gain)  # -1 sets gain to auto
    if args.gamma is not None:
        cap.set(cv2.CAP_PROP_GAMMA, args.gamma)
    if args.fps is not None:
        cap.set(cv2.CAP_PROP_FPS, args.fps)
    if args.brightness is not None:
        cap.set(cv2.CAP_PROP_BRIGHTNESS, args.brightness)

    # Window setting
    winname = "press q to quit"
    cv2.namedWindow(winname)
    # Mouse event setting
    cv2.setMouseCallback(winname, print_xy, args.scale)

    # Start capturing
    while True:
        ret, frame = cap.read()
        # frame = cv2.cvtColor(frame, cv2.COLOR_BayerBG2BGR) #for RGB camera demosaicing

        img_show = cv2.resize(frame, None, fx=args.scale, fy=args.scale)
        cv2.imshow(winname, img_show)
        key = cv2.waitKey(30)
        if key == ord("q"):
            break

    cv2.destroyAllWindows()
    cap.release()


if __name__ == "__main__":
    main()
