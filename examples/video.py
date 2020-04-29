import EasyPySpin
import cv2
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--index", type=int, default=0, help="Camera index (Default: 0)")
    parser.add_argument("-e", "--exposure",type=float, default=-1, help="Exposure time [us] (Default: Auto)")
    parser.add_argument("-g", "--gain", type=float, default=-1, help="Gain [dB] (Default: Auto)")
    parser.add_argument("-G", "--gamma", type=float, help="Gamma value")
    parser.add_argument("-b", "--brightness", type=float, help="Brightness [EV]")
    parser.add_argument("-f", "--fps", type=float, help="FrameRate [fps]")
    parser.add_argument("-s", "--scale", type=float, default=0.25, help="Image scale to show (>0) (Default: 0.25)")
    args = parser.parse_args()

    cap = EasyPySpin.VideoCapture(args.index)

    if not cap.isOpened():
        print("Camera can't open\nexit")
        return -1
    
    cap.set(cv2.CAP_PROP_EXPOSURE, args.exposure) #-1 sets exposure_time to auto
    cap.set(cv2.CAP_PROP_GAIN, args.gain) #-1 sets gain to auto
    if args.gamma      is not None: cap.set(cv2.CAP_PROP_GAMMA, args.gamma)
    if args.fps        is not None: cap.set(cv2.CAP_PROP_FPS, args.fps)
    if args.brightness is not None: cap.set(cv2.CAP_PROP_BRIGHTNESS, args.brightness)

    while True:
        ret, frame = cap.read()

        img_show = cv2.resize(frame, None, fx=args.scale, fy=args.scale)
        cv2.imshow("capture", img_show)
        key = cv2.waitKey(30)
        if key==ord("q"):
            break
        elif key==ord("c"):
            import datetime
            time_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            filepath = time_stamp + ".png"
            cv2.imwrite(filepath, frame)
            print("Export > ", filepath)
    
    cv2.destroyAllWindows()
    cap.release()

if __name__=="__main__":
    main()
