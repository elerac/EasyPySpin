import cv2
import PySpin
import EasyPySpin

def main():
    cap = EasyPySpin.VideoCapture(0)
    cam = cap.cam

    cam.TriggerMode.SetValue(True)
    cam.TriggerSelector.SetValue(PySpin.TriggerSelector_FrameStart)
    cam.TriggerSource.SetValue(PySpin.TriggerSource_Software)
    cam.BeginAcquisition()

    while True:
        cam.TriggerSoftware.Execute()
        ret, frame = cap.read()

        img_show = cv2.resize(frame, None, fx=0.25, fy=0.25)
        cv2.imshow("capture", img_show)
        key = cv2.waitKey(30)
        if key==ord("q"):
            break
    
    cv2.destroyAllWindows()

if __name__=="__main__":
    main()
