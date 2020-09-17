"""
Example of capturing the average image width VideoCaptureEX class.
Noise can be reduced by capturing multiple images and computing the average of each pixel.
"""
import EasyPySpin
import cv2

def main():
    cap = EasyPySpin.VideoCaptureEX(0)
    
    print("Press key to change average number")
    print("k : average_num += 1")
    print("j : average_num -= 1")
    print("--------------------")
    print("average num: ", cap.average_num)
    
    while True:
        ret, frame = cap.read()

        img_show = cv2.resize(frame, None, fx=0.25, fy=0.25)
        cv2.imshow("press q to quit", img_show)
        
        key = cv2.waitKey(30)
        if key==ord("q"):
            break
        elif key==ord("k"):
            cap.average_num += 1
            print("average num: ", cap.average_num)
        elif key==ord("j"):
            cap.average_num -= 1
            if cap.average_num<1:
                cap.average_num = 1
            print("average num: ", cap.average_num)
    
    cv2.destroyAllWindows()
    cap.release()

if __name__=="__main__":
    main()
