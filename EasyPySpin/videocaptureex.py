import cv2
import PySpin
import numpy as np
from .videocapture import VideoCapture

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
    

    def readHDR(self, t_min, t_max, num, t_ref=0.0166):
        """
        Capture multiple images with different exposure and merge into an HDR image

        NOTE: A software trigger is used to capture images. In order to acquire an image reliably at the set exposure time.

        Parameters
        ----------
        t_min : float
            minimum exposure time
        t_max : float
            maximum exposure time
        num : int
            number of shots
        t_ref : float, optional
            Reference time. Determines the brightness of the merged image based on this time.

        Returns
        -------
        retval : bool
            false if no frames has been grabbed.
        image_hdr : array_like 
            merged HDR image is returned here. If no image has been grabbed the image will be None.
        """
        # Original settings for gamma
        gamma_origin = self.get(cv2.CAP_PROP_GAMMA)

        # To capture a linear image, the gamma value is set to 1.0
        self.set(cv2.CAP_PROP_GAMMA, 1.0)

        # Exposure time to be taken 
        # The equality sequence from minimum (t_min) to maximum (t_max) exposure time
        times_us = np.geomspace(t_min, t_max, num=num)
       
        # Exposure bracketing
        ret, imlist = self.readExposureBracketing(times_us)
        if ret==False:
            return False, None
        
        # Restore the changed gamma
        self.set(cv2.CAP_PROP_GAMMA, gamma_origin)
        
        # Normalize to a value between 0 and 1
        # By dividing by the maximum value
        dtype = imlist[0].dtype
        if dtype==np.uint8:
            max_value = 2**8-1
        elif dtype==np.uint16:
            max_value = 2**16-1
        else:
            max_value = 1
        imlist_norm = [ image/max_value for image in imlist]
        
        # Merge HDR
        img_hdr = self.mergeHDR(imlist_norm, times_us*1e-6, t_ref)

        return True, img_hdr
   

    def readExposureBracketing(self, exposures):
        """
        Execute exposure bracketing.

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
        TriggerSelector_origin = self.cam.TriggerSelector.GetValue()
        TriggerMode_origin = self.cam.TriggerMode.GetValue()
        TriggerSource_origin = self.cam.TriggerSource.GetValue()
        auto_software_trigger_execute_origin = self.auto_software_trigger_execute
        ExposureAuto_origin = self.cam.ExposureAuto.GetValue()
        ExposureTime_origin = self.cam.ExposureTime.GetValue()
        GainAuto_origin = self.cam.GainAuto.GetValue()
        Gain_origin = self.cam.Gain.GetValue()
        
        # Change the trigger setting
        self.cam.TriggerSelector.SetValue(PySpin.TriggerSelector_FrameStart)
        self.cam.TriggerMode.SetValue(PySpin.TriggerMode_On)
        self.cam.TriggerSource.SetValue(PySpin.TriggerSource_Software)
        self.auto_software_trigger_execute = True

        # Auto gain off and fixing gain
        self.cam.GainAuto.SetValue(PySpin.GainAuto_Off)
        self.cam.Gain.SetValue(Gain_origin)
        
        # Capture start
        imlist = [None]*exposures.shape[0]
        for i , t in enumerate(exposures):
            self.set(cv2.CAP_PROP_EXPOSURE, float(t))

            ret, frame = self.read()

            if ret==False:
                return False, None

            imlist[i] = frame
       
        # Restore the changed settings
        self.cam.TriggerSelector.SetValue(TriggerSelector_origin)
        self.cam.TriggerMode.SetValue(TriggerMode_origin)
        self.cam.TriggerSource.SetValue(TriggerSource_origin)
        self.auto_software_trigger_execute = auto_software_trigger_execute_origin
        self.cam.ExposureTime.SetValue(ExposureTime_origin)
        self.cam.ExposureAuto.SetValue(ExposureAuto_origin)
        self.cam.GainAuto.SetValue(GainAuto_origin)

        return True, imlist

   
    def mergeHDR(self, imlist, times, time_ref=0.0166, weighting='photon'):
        """
        Merge an HDR image from LDR images.

        Parameters
        ----------
        imlist : List[array_like]
            Multiple images with different exposure. The images are a range of 0.0 to 1.0.
        times : array_like
            Exposure times
        time_ref : float, optional
            Reference time. Determines the brightness of the merged image based on this time.
        weighting : str, {'uniform', 'tent', 'gaussian', 'photon'}, optional
            Weighting scheme
        
        Returns
        -------
        img_hdr : array_like
            merged HDR image is returned here.
        """
        Zmin = 0.01
        Zmax = 0.99
        epsilon = 1e-32
        z = np.array(imlist) # (num, height, width)
        t = (np.array(times) / time_ref)[:, np.newaxis, np.newaxis] # (num,1,1)

        # Calculate weight
        mask = np.bitwise_and(Zmin<=z, z<=Zmax)
        if   weighting=='uniform':
            w = 1.0 * mask
        elif weighting=='tent':
            w = (0.5-np.abs(z-0.5)) * mask
        elif weighting=='gaussian':
            w = np.exp(-4*((z-0.5)/0.5)**2) * mask
        elif weighting=='photon':
            w = t*np.ones_like(z) * mask
        else:
            raise ValueError(f"Unknown weighting scheme '{weighting}'.")
        
        # Merge HDR
        img_hdr = np.sum(w*z/t, axis=0) / (np.sum(w, axis=0) + epsilon)
        #img_hdr = np.exp(np.sum(w*(np.log(z+epsilon)-np.log(t)), axis=0)/(np.sum(w, axis=0)+1e-32))

        # Dealing with under-exposure and over-exposure
        under_exposed = np.all(Zmin>z, axis=0)
        over_exposed  = np.all(z>Zmax, axis=0)
        img_hdr[under_exposed] = Zmin/np.max(t)
        img_hdr[over_exposed]  = Zmax/np.min(t)

        return img_hdr
