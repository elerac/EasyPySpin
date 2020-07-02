import EasyPySpin
import cv2

SCALE = 0.5

def main():
    cap_primary = EasyPySpin.VideoCapture(0)
    cap_secondary = EasyPySpin.VideoCapture(1)

    cap_primary.set(cv2.CAP_PROP_TRIGGER, True) #TriggerMode -> On
    #import PySpin
    #cap_primary.cam.TriggerSource.SetValue(PySpin.TriggerSource_Software)

    cap_sync = EasyPySpin.SynchronizedVideoCapture(cap_primary, cap_secondary)

    while True:
        ret, frame = cap_sync.read()
        frame_primary = frame[0]
        frame_secondary = frame[1]

        img_show_primary = cv2.resize(frame_primary, None, fx=SCALE, fy=SCALE)
        img_show_secondary = cv2.resize(frame_secondary, None, fx=SCALE, fy=SCALE)
        cv2.imshow("primary", img_show_primary)
        cv2.imshow("secondary", img_show_secondary)
        key = cv2.waitKey(1)
        if key==ord("q"):
            break
        elif key==ord("c"):
            import datetime
            time_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            filename0 = "synchronized-{0}-{1}.png".format(time_stamp, 0)
            filename1 = "synchronized-{0}-{1}.png".format(time_stamp, 1)
            cv2.imwrite(filename0, frame_primary)
            cv2.imwrite(filename1, frame_secondary)
            print("Image saved at {}".format(filename0))
            print("Image saved at {}".format(filename1))
            print()
    
    cv2.destroyAllWindows()
    cap_sync.release()

if __name__=="__main__":
    main()
