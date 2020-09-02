import cv2
import PySpin
from .videocapture import VideoCapture

class VideoCaptureEX(VideoCapture):
    """
    VideoCaptureEX class is subclass of VideoCapture class.
    It provides extensions that are not supported by OpenCV's VideoCapture.
    """

    def read(self, N=1):
        """
        returns the next frame.
        The returned frame is the average of multiple images taken.

        Parameters
        ----------
        N : int
            average number

        Returns
        -------
        retval : bool
            false if no frames has been grabbed.
        image : array_like 
            grabbed image is returned here. If no image has been grabbed the image will be None.
        """
        imlist = [ super(VideoCaptureEX, self).read()[1] for i in range(N) ]
        frame = (cv2.merge(imlist).mean(axis=2)).astype(imlist[0].dtype)
        return True, frame
