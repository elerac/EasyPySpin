import EasyPySpin
import cv2

NUM_IMAGES = 10

def main():
    cap0 = EasyPySpin.VideoCapture(0)
    cap1 = EasyPySpin.VideoCapture(1)
    
    for n in range(NUM_IMAGES):
        ret0, frame0 = cap0.read()
        ret1, frame1 = cap1.read()

        filename0 = "multiple-{0}-{1}.png".format(n, 0)
        filename1 = "multiple-{0}-{1}.png".format(n, 1)
        cv2.imwrite(filename0, frame0)
        cv2.imwrite(filename1, frame1)
        print("Image saved at {}".format(filename0))
        print("Image saved at {}".format(filename1))
        print()

    cap0.release()
    cap1.release()

if __name__=="__main__":
    main()
