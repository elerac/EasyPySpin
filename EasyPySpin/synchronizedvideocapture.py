from typing import Tuple, Union

from .multiplevideocapture import MultipleVideoCapture


class SynchronizedVideoCapture(MultipleVideoCapture):
    """VideoCapture for hardware synchronized cameras.

    I only have the "BFS" camera, so I haven't tested it with any other camera ("BFLY", "CM3", etc...). So, if you have a problem, please send me an issue or PR.

    Notes
    -----
    You can find instructions on how to connect the camera in FLIR official page.
    https://www.flir.com/support-center/iis/machine-vision/application-note/configuring-synchronized-capture-with-multiple-cameras

    Examples
    --------
    Case1: The pair of primary and secondary cameras.

    >>> serial_number_1 = "20541712"  # primary camera
    >>> serial_number_2 = "19412150"  # secondary camera
    >>> cap = EasyPySpin.SynchronizedVideoCapture(serial_number_1, serial_number_2)
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

    Case2: The secondary camera and external trigger.

    >>> serial_number = "19412150"  # secondary camera
    >>> cap = EasyPySpin.SynchronizedVideoCapture(None, serial_number_2)

    Case3: The two (or more) secondary cameras and external trigger.

    >>> serial_number_1 = "20541712"  # secondary camera 1
    >>> serial_number_2 = "19412150"  # secondary camera 2
    >>> cap = EasyPySpin.SynchronizedVideoCapture(None, serial_number_1, serial_number_2)
    """

    def __init__(
        self,
        index_primary: Union[int, str],
        *indexes_secondary: Tuple[Union[int, str], ...]
    ):
        if index_primary is not None:
            self.open_as_primary(index_primary)

        for index_secondary in indexes_secondary:
            self.open_as_secondary(index_secondary)

    def open_as_primary(self, index: Union[int, str]) -> bool:
        self.open(index)
        cap = self[-1]
        cap._configure_as_primary()
        return cap.isOpened()

    def open_as_secondary(self, index: Union[int, str]) -> bool:
        self.open(index)
        cap = self[-1]
        cap._configure_as_secondary()
        return cap.isOpened()
