from typing import Union, Tuple, List

import numpy as np
import cv2
import PySpin

from .videocapture import VideoCapture
from .utils import warn

class VideoCaptureEX(VideoCapture):
    """
    VideoCaptureEX class is subclass of VideoCapture class.
    It provides extensions that are not supported by OpenCV's VideoCapture.
    
    Attributes
    ----------
    cam : PySpin.CameraPtr
        camera
    nodemap : PySpin.INodeMap
        nodemap represents the elements of a camera description file.
    grabTimeout : uint64_t
        a 64bit value that represents a timeout in milliseconds
    streamID : uint64_t
        The stream to grab the image.
    auto_software_trigger_execute : bool
        Whether or not to execute a software trigger when executing "read()".
        When the "TriggerMode" is "On" and the "TriggerSource" is set to "Software". (Default: False)
    average_num : int
        average number

    Methods
    -------
    read()
        returns the next frame.
    release()
        Closes capturing device.
    isOpened()
        Whether a camera is open or not.
    set(propId, value)
        Sets a property.
    get(propId)
        Gets a property.
    """
    def __init__(self, index):
        """
        Parameters
        ----------
        index : int
            id of the video capturing device to open.
        """
        super(VideoCaptureEX, self).__init__(index)
        self.average_num = 1

    def read(self):
        """
        returns the next frame.
        The returned frame is the average of multiple images taken.

        Returns
        -------
        retval : bool
            false if no frames has been grabbed.
        image : array_like 
            grabbed image is returned here. If no image has been grabbed the image will be None.
        """
        if self.average_num==1:
            return super(VideoCaptureEX, self).read()
        else:
            imlist = [ super(VideoCaptureEX, self).read()[1] for i in range(self.average_num) ]
            frame = (cv2.merge(imlist).mean(axis=2)).astype(imlist[0].dtype)
            return True, frame
    


    def readHDR(self, t_min: float, t_max: float, t_ref: float = 10000, ratio: float = 2.0) -> Tuple[bool, np.ndarray]:
        """Capture multiple images with different exposure and merge into an HDR image.

        Parameters
        ----------
        t_min : float
            Minimum exposure time [us]
        t_max : float
            Maximum exposure time [us]
        t_ref : float, default=10000
            Reference time [us]. 
            Determines the brightness of the merged image based on this time.
        ratio : int, default=2.0
            Ratio of exposure time.
            Number of shots is automatically determined from `t_min` and `t_max`. 
            It is set so that the `ratio` of neighboring exposure times.

        Returns
        -------
        retval : bool
            false if no frames has been grabbed.
        image_hdr : np.ndarray
            merged HDR image is returned here. If no image has been grabbed the image will be None.

        Notes
        -----
        A software trigger is used to capture images. In order to acquire an image reliably at the set exposure time.
        """
        # Set between the maximum and minimum values of the camera
        t_min = np.clip(t_min, self.cam.ExposureTime.GetMin(), self.cam.ExposureTime.GetMax())
        t_max = np.clip(t_max, self.cam.ExposureTime.GetMin(), self.cam.ExposureTime.GetMax())    
        
        # Determine nnumber of shots
        num = 2
        if ratio > 1.0:
            while t_max > t_min*(ratio**num):
                num += 1

        # Exposure time to be taken 
        # The equality sequence from minimum (t_min) to maximum (t_max) exposure time
        times = np.geomspace(t_min, t_max, num=num)

        # Original settings for gamma
        gamma_origin = self.get(cv2.CAP_PROP_GAMMA)

        # To capture a linear image, the gamma value is set to 1.0
        self.set(cv2.CAP_PROP_GAMMA, 1.0)
       
        # Exposure bracketing
        ret, imlist = self.readExposureBracketing(times)

        # Restore the changed gamma
        self.set(cv2.CAP_PROP_GAMMA, gamma_origin)

        if not ret:
            return False, None
        
        # Normalize to a value between 0 and 1
        # By dividing by the maximum value
        dtype = imlist[0].dtype
        if dtype == np.uint8:
            max_value = float(2**8-1)
        elif dtype == np.uint16:
            max_value = float(2**16-1)
        else:
            max_value = 1.0
        imlist_norm = [ image/max_value for image in imlist]
        
        # Merge HDR
        img_hdr = self.mergeHDR(imlist_norm, times, t_ref)

        return True, img_hdr.astype(np.float32)

    def readExposureBracketing(self, exposures: np.ndarray) -> Tuple[bool, List[np.ndarray]]:
        """Execute exposure bracketing.

        Parameters
        ----------
        exposures : array_like
            Exposure times

        Returns
        -------
        retval : bool
            false if no frames has been grabbed
        imlist : List[array_like]
            Captured image list
        """
        # Original settings for triggers, exposure, gain
        node_names_to_change = ["TriggerSelector", "TriggerMode", "TriggerSource", "ExposureTime", "ExposureAuto", "GainAuto"] 
        values_origin = [self.get_pyspin_value(node_name) for node_name in node_names_to_change]
        auto_software_trigger_execute_origin = self.auto_software_trigger_execute
        
        # Change the trigger setting
        self.set_pyspin_value("TriggerSelector", "FrameStart")
        self.set_pyspin_value("TriggerMode", "On")
        self.set_pyspin_value("TriggerSource", "Software")
        self.auto_software_trigger_execute = True

        # Auto gain off and fixing gain
        gain = self.get_pyspin_value("Gain")
        self.set_pyspin_value("GainAuto", "Off")
        self.set_pyspin_value("Gain", gain)
        
        # Capture start
        imlist = []
        for i, t in enumerate(exposures):
            self.set(cv2.CAP_PROP_EXPOSURE, float(t))

            # Dummy image
            if i == 0:
                for _ in range(3):
                    self.grab()

            ret, frame = self.read()

            if not ret:
                return False, None

            imlist.append(frame)

        self.cam.EndAcquisition()

        # Restore the changed settings
        for node_name, value in zip(node_names_to_change, values_origin):
            self.set_pyspin_value(node_name, value)
        self.auto_software_trigger_execute = auto_software_trigger_execute_origin

        return True, imlist

    def mergeHDR(self, imlist: List[np.ndarray], times: np.ndarray, time_ref: float = 10000) -> np.ndarray:
        """
        Merge an HDR image from LDR images.

        Parameters
        ----------
        imlist : List[np.ndarray]
            Multiple images with different exposure. The images are a range of 0.0 to 1.0.
        times : np.ndarray
            Exposure times
        time_ref : float, optional
            Reference time. Determines the brightness of the merged image based on this time.
        
        Returns
        -------
        img_hdr : np.ndarray
            merged HDR image is returned here.
        """
        Zmin = 0.01
        Zmax = 0.99
        epsilon = 1e-32
        
        z = np.array(imlist) # (num, height, width) or (num, height, width, ch)

        t = np.array(times) / time_ref # (num, )
        t = np.expand_dims(t, axis=tuple(range(1, z.ndim))) # (num, 1, 1) or (num, 1, 1, 1)

        # Calculate gaussian weight
        mask = np.bitwise_and(Zmin<=z, z<=Zmax)
        w = np.exp(-4*((z-0.5)/0.5)**2) * mask

        # Merge HDR
        img_hdr = np.average(z/t, axis=0, weights=w+epsilon)

        # Dealing with under-exposure and over-exposure
        under_exposed = np.all(Zmin>z, axis=0)
        over_exposed  = np.all(z>Zmax, axis=0)
        img_hdr[under_exposed] = Zmin/np.max(t)
        img_hdr[over_exposed]  = Zmax/np.min(t)

        return img_hdr