"""
Example of capturing the HDR image width VideoCaptureEX class
"""
import EasyPySpin
import cv2
import numpy as np
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--index", type=int, default=0, help="Camera index (Default: 0)")
    parser.add_argument("-g", "--gain", type=float, default=0, help="Gain [dB] (Default: 0)")
    parser.add_argument("--min", type=float, default=5000, help="Minimum exposure time [us]")
    parser.add_argument("--max", type=float, default=500000, help="Maximum exposure time [us]")
    parser.add_argument("--num", type=int, default=8, help="Number of images to capture")
    parser.add_argument("-o", "--output", type=str, default="capture_hdr.exr", help="Output file name (*.exr)")
    args = parser.parse_args()

    cap = EasyPySpin.VideoCaptureEX(args.index)
    
    cap.set(cv2.CAP_PROP_GAMMA, 1.0)
    cap.set(cv2.CAP_PROP_GAIN, args.gain)
    
    print("Start capturing HDR image")
    ret, img_hdr = cap.readHDR(args.min, args.max, args.num) 
    
    print("Write {}".format(args.output))
    cv2.imwrite(args.output, img_hdr.astype(np.float32))

if __name__=="__main__":
    main()
