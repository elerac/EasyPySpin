import EasyPySpin
import cv2
import numpy as np
import argparse

def merge_hdr(images, times, maximum_value=255):
    Zmin = 0.01
    Zmax = 0.99
    I = np.array(images) #(num, height, width, color)
    t = np.array(times) #(num,)

    #Calculate weight
    z = I/maximum_value
    mask = np.bitwise_and(Zmin<=z, z<=Zmax)
    #w = 1.0 * mask #uniform
    #w = (0.5-np.abs(z-0.5)) * mask #tent
    w = np.exp(-4*((z-0.5)/0.5)**2) * mask #Gaussian

    #Merge
    if I.ndim==3: #Gray
        _t = t[:,np.newaxis,np.newaxis]
    else: #RGB
        _t = t[:,np.newaxis,np.newaxis,np.newaxis]
    I_HDR = np.sum(w*I/_t, axis=0)/(np.sum(w, axis=0)+1e-32)
    #I_HDR = np.exp(np.sum(w*(np.log(I+1e-32)-np.log(_t)), axis=0)/(np.sum(w, axis=0)+1e-32))

    #Dealing with under-exposure and over-exposure
    under_exposed = np.all(Zmin>z, axis=0)
    over_exposed  = np.all(z>Zmax, axis=0)
    I_HDR[under_exposed] = Zmin*maximum_value/np.max(t)
    I_HDR[over_exposed]  = Zmax*maximum_value/np.min(t)

    return I_HDR

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--index", type=int, default=0, help="Camera index (Default: 0)")
    parser.add_argument("-g", "--gain", type=float, default=0, help="Gain [dB] (Default: 0)")
    parser.add_argument("--min", type=float, default=50000, help="Minimum exposure time [us]")
    parser.add_argument("--max", type=float, default=500000, help="Minimum exposure time [us]")
    parser.add_argument("--num", type=float, default=5, help="Number of images to capture")
    parser.add_argument("-o", "--output", type=str, default="hdr.exr", help="Output file name (*.exr)")
    args = parser.parse_args()

    cap = EasyPySpin.VideoCapture(args.index)
    
    cap.set(cv2.CAP_PROP_GAMMA, 1.0)
    cap.set(cv2.CAP_PROP_GAIN, args.gain)
    
    times_us = np.geomspace(args.min, args.max, num=args.num).tolist()

    print("Start capturing")
    images = []
    for i, time_to_set in enumerate(times_us):
        cap.set(cv2.CAP_PROP_EXPOSURE, time_to_set)

        _ = cap.read() #Ignore first frame (Because it may be the image taken before the exposure time was changed)
        
        ret, frame = cap.read()
        images.append(frame)
        
        print("Image {0}/{1}".format(i+1, args.num))
        print("    ExposureTime: {}\n".format(time_to_set))
    
    cap.release()
    print("End capturing\n")
    
    print("Merge HDR")
    times = [t*(1e-6) for t in times_us] #us -> s
    img_hdr = merge_hdr(images, times)
    
    print("Write {}".format(args.output))
    cv2.imwrite(args.output, img_hdr.astype(np.float32))

if __name__=="__main__":
    main()
