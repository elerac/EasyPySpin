"""Example of capturing the HDR image width VideoCaptureEX class
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
    parser.add_argument("-o", "--output", type=str, default="hdr", help="Output file name")
    args = parser.parse_args()

    cap = EasyPySpin.VideoCaptureEX(args.index)
    cap.set(cv2.CAP_PROP_GAIN, args.gain)

    print("Start capturing HDR image")
    ret, img_hdr = cap.readHDR(args.min, args.max)

    filename_exr = f"{args.output}.exr"
    print(f"Write {filename_exr}")
    cv2.imwrite(filename_exr, img_hdr.astype(np.float32))

    for ev in [-2, -1, 0, 1, 2]:
        sign = "+" if ev >= 0 else "-"
        filename_png = f"{args.output}_{sign}{abs(ev)}EV.png"
        ratio = 2.0 ** ev
        img_hdr_u8 = np.clip(img_hdr * ratio * 255, 0, 255).astype(np.uint8)

        print(f"Write {filename_png}")
        cv2.imwrite(filename_png, img_hdr_u8)

    cap.release()


if __name__ == "__main__":
    main()
