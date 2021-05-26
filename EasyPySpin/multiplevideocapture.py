from typing import List, Tuple, Union
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import PySpin

from .videocapture import VideoCapture

class MultipleVideoCapture:
    """VideoCapture for Multiple cameras.

    Examples
    --------
    >>> cap = MultipleVideoCapture(0)
    >>> cap.isOpened()
    [True]
    >>> cap = MultipleVideoCapture(0, 1)
    >>> cap.isOpened()
    [True, True]
    >>> cap.set(cv2.CAP_PROP_EXPOSURE, 1000)
    [True, True]
    >>> cap.get(cv2.CAP_PROP_EXPOSURE)
    [1000.0, 1000.0]
    >>> cap[0].set(cv2.CAP_PROP_EXPOSURE, 2000)
    True
    >>> cap.get(cv2.CAP_PROP_EXPOSURE)
    [2000.0, 1000.0]
    >>> (ret0, frame0), (ret1, frame1) = cap.read()
    >>> cap.release()
    """

    VideoCaptureBase = VideoCapture
    __caps = [None]
    
    def __init__(self, *indexes: Tuple[Union[int, str], ...]):
        self.open(*indexes)

    def __del__(self):
        return [cap.__del__() for cap in self]

    def __len__(self):
        return self.__caps.__len__()

    def __getitem__(self, item):
        return self.__caps.__getitem__(item)

    def __iter__(self):
        return self.__caps.__iter__()

    def __next__(self):
        return self.__caps.__next__()

    def __setattr__(self, key, value):
        for cap in self:
            if hasattr(cap, key):
                setattr(cap, key, value)
        
        return object.__setattr__(self, key, value)

    def open(self, *indexs: Tuple[Union[int, str], ...]) -> List[bool]:
        self.__caps = [self.VideoCaptureBase(index) for index in indexs]
        return self.isOpened()

    def isOpened(self) -> List[bool]:
        return [cap.isOpened() for cap in self]

    def grab(self) -> List[bool]:
        return [cap.grab() for cap in self]

    def retrieve(self) -> List[Tuple[bool, Union[np.ndarray, None]]]:
        return [cap.retrieve() for cap in self]

    def read(self) -> List[Tuple[bool, Union[np.ndarray, None]]]:
        #return [cap.read() for cap in self]
        executor = ThreadPoolExecutor()
        futures = [executor.submit(cap.read) for cap in self]
        executor.shutdown()
        return [future.result() for future in futures]

    def release(self) -> List[None]:
        return self.__del__()

    def set(self, propId: "cv2.VideoCaptureProperties", value: any) -> List[bool]:
        return [cap.set(propId, value) for cap in self]
    
    def get(self, propId: "cv2.VideoCaptureProperties") -> List[any]:
        return [cap.get(propId) for cap in self]

    def setExceptionMode(self, enable: bool) -> List[None]:
        return [cap.setExceptionMode(enable) for cap in self]

    def set_pyspin_value(self, node_name: str, value: any) -> List[any]:
        return [cap.set_pyspin_value(node_name, value) for cap in self]
    
    def get_pyspin_value(self, node_name: str) -> List[any]:
        return [cap.get_pyspin_value(node_name) for cap in self]
