from typing import List, Tuple, Union, Any
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import PySpin

from .videocapture import VideoCapture as EasyPySpinVideoCapture


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

    __caps = list()
    __executor = ThreadPoolExecutor()

    def __init__(self, *indexes: Tuple[Union[int, str], ...]):
        self.open(*indexes)

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

    def __getattr__(self, name):
        def method(*args, **kwargs) -> List[Any]:
            futures = [
                self.__executor.submit(getattr(cap, name), *args, **kwargs)
                for cap in self
            ]
            return [future.result() for future in futures]

        return method

    def open(
        self, *indexs: Tuple[Union[int, str], ...], VideoCapture=EasyPySpinVideoCapture
    ) -> List[bool]:
        for index in indexs:
            cap = VideoCapture(index)
            self.__caps.append(cap)

        return self.isOpened()
