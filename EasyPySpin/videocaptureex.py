import cv2
import PySpin
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
