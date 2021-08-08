import warnings
from typing import Union, Tuple

import numpy as np
import cv2
import PySpin

from .utils import EasyPySpinWarning, warn


class VideoCapture:
    """Open a FLIR camera for video capturing.

    Attributes
    ----------
    cam : PySpin.CameraPtr
        PySpin camera pointer.
    grabTimeout : int, default=PySpin.EVENT_TIMEOUT_INFINITE
        a 64bit value that represents a timeout in milliseconds
    streamID : int, default=0
        The stream to grab the image.
    auto_software_trigger_execute : bool, default=False
        Whether or not to execute a software trigger when executing ``grab()``.
        When the SoftwareTrigger is available.

    Methods
    -------
    get(propId)
        Gets a property.
    grab()
        Grabs the next frame from capturing device.
    isOpened()
        Whether a camera is open or not.
    open()
        Open a capturing device for video capturing.
    read()
        Returns the next frame.
    release()
        Closes capturing device.
    retrieve()
        Decodes and returns the grabbed video frame.
    set(propId, value)
        Sets a property.
    setExceptionMode(enable)
        Switches exceptions mode.

    Notes
    -----
    Supported ``cv2.VideoCaptureProperties`` for ``set()`` or ``get()`` methods.
    `cv2.CAP_PROP_FPS`
    `cv2.CAP_PROP_FRAME_WIDTH`
    `cv2.CAP_PROP_FRAME_HEIGHT`
    `cv2.CAP_PROP_BRIGHTNESS`
    `cv2.CAP_PROP_GAIN`
    `cv2.CAP_PROP_EXPOSURE`
    `cv2.CAP_PROP_GAMMA`
    `cv2.CAP_PROP_TEMPERATURE` (get only)
    `cv2.CAP_PROP_TRIGGER`
    `cv2.CAP_PROP_TRIGGER_DELAY`
    `cv2.CAP_PROP_BACKLIGHT`
    `cv2.CAP_PROP_AUTO_WB`
    """

    # a 64bit value that represents a timeout in milliseconds
    grabTimeout: int = PySpin.EVENT_TIMEOUT_INFINITE

    # The stream to grab the image.
    streamID: int = 0

    # Whether or not to execute a software trigger when executing ``grab()``.
    auto_software_trigger_execute: bool = False

    def __init__(self, index: Union[int, str] = None):
        """
        Parameters
        ----------
        index : int or str, default=None
            For ``int`` type, the index at which to retrieve the camera object.
            For ``str`` type, the serial number of the camera object to retrieve.
        """
        if index is not None:
            self.open(index)

    @property
    def cam(self) -> Union[PySpin.CameraPtr, None]:
        """Provide ``PySpin.CameraPtr``."""
        if hasattr(self, "_cam"):
            return self._cam
        else:
            return None

    def open(self, index: Union[int, str]) -> bool:
        """Open a capturing device for video capturing.

        Parameters
        ----------
        index : int or str
            ``int`` type, the index at which to retrieve the camera object.
            ``str`` type, the serial number of the camera object to retrieve.

        Returns
        -------
        retval : bool
            ``True`` if the file has been successfully opened.
        """
        # Close the already opened camera
        self.release()

        # Cerate system instance and get camera list
        self._system = PySpin.System.GetInstance()
        self._cam_list = self._system.GetCameras()
        num_cam = self._cam_list.GetSize()

        # Check for available cameras
        if num_cam == 0:
            warn("no camera is available")
            self.release()
            return False

        # Get CameraPtr
        if type(index) is int:
            if index in range(num_cam):
                self._cam = self._cam_list.GetByIndex(index)
            else:
                warn(f"out device of bound (0-{num_cam-1}): {index}")
                self.release()
                return False
        elif type(index) is str:
            self._cam = self._cam_list.GetBySerial(index)
        else:
            warn(f"'index' must be 'int' or 'str', not '{type(index).__name__}'")
            self.release()
            return False

        if not self._cam.IsValid():
            self.release()
            return False

        # Initialize camera
        if not self.cam.IsInitialized():
            self.cam.Init()

        # Switch 'StreamBufferHandlingMode' to 'NewestOnly'.
        # This setting allows acquisition of the latest image
        # by ignoring old images in the buffer, just like a web cam.
        self.cam.TLStream.StreamBufferHandlingMode.SetValue(
            PySpin.StreamBufferHandlingMode_NewestOnly
        )

        return True

    def __del__(self):
        try:
            if hasattr(self, "_cam"):
                if self._cam.IsStreaming():
                    self._cam.EndAcquisition()
                del self._cam

            if hasattr(self, "_cam_list"):
                self._cam_list.Clear()

            if hasattr(self, "_system"):
                if not self._system.IsInUse():
                    self._system.ReleaseInstance()
                    del self._system

        except PySpin.SpinnakerException:
            pass

    def release(self) -> None:
        """Closes capturing device. The method call VideoCapture destructor."""
        self.__del__()

    def isOpened(self) -> bool:
        """Returns ``True`` if video capturing has been initialized already.

        Returns
        -------
        retval : bool
        """
        if self.cam is not None:
            try:
                return self.cam.IsValid()
            except AttributeError:
                return False
        else:
            return False

    def grab(self) -> bool:
        """Grabs the next frame from capturing device.

        Returns
        -------
        retval : bool
            ``True`` the case of success.
        """
        if not self.isOpened():
            return False

        if not self.cam.IsStreaming():
            self.cam.BeginAcquisition()

        # Execute a software trigger if required
        if (
            PySpin.IsAvailable(self.cam.TriggerSoftware)
            and self.auto_software_trigger_execute
        ):
            # Software-Trigger is executed under TWO conditions.
            # First, the TriggerMode is set to ``On``
            # and the TriggerSource is set to ``Software``,
            # so that SoftwareTrigger is available.
            # Second, the member variable ``auto_software_trigger_execute``  is set to ``True``.
            self.cam.TriggerSoftware.Execute()

        # Grab image
        self._pyspin_image = self.cam.GetNextImage(self.grabTimeout, self.streamID)

        is_complete = not self._pyspin_image.IsIncomplete()
        return is_complete

    def retrieve(self) -> Tuple[bool, Union[np.ndarray, None]]:
        """Decodes and returns the grabbed video frame.

        Returns
        -------
        retval : bool
            ``False`` if no frames has been grabbed.
        image : np.ndarray
            grabbed image is returned here. If no image has been grabbed the image will be None.
        """
        if hasattr(self, "_pyspin_image"):
            image_array = self._pyspin_image.GetNDArray()
            return True, image_array
        else:
            return False, None

    def read(self) -> Tuple[bool, Union[np.ndarray, None]]:
        """Grabs, decodes and returns the next video frame.

        The method combines ``grab()`` and ``retrieve()`` in one call.
        This is the most convenient method for capturing data from decode and returns the just grabbed frame.
        If no frames has been grabbed, the method returns ``False`` and the function returns ``None``.

        Returns
        -------
        retval : bool
            ``False`` if no frames has been grabbed.
        image : np.ndarray
            grabbed image is returned here. If no image has been grabbed the image will be ``None``.
        """
        retval = self.grab()
        if retval:
            return self.retrieve()
        else:
            return False, None

    def set(self, propId: "cv2.VideoCaptureProperties", value: any) -> bool:
        """Sets a property in the VideoCapture.

        Parameters
        ----------
        propId_id : cv2.VideoCaptureProperties
            Property identifier from cv2.VideoCaptureProperties.
        value : int or float or bool
            Value of the property.

        Returns
        -------
        retval : bool
           True if property setting success.
        """
        # Width setting
        if propId == cv2.CAP_PROP_FRAME_WIDTH:
            return self.set_pyspin_value("Width", value)

        # Height setting
        if propId == cv2.CAP_PROP_FRAME_HEIGHT:
            return self.set_pyspin_value("Height", value)

        # FrameRate setting
        if propId == cv2.CAP_PROP_FPS:
            is_success1 = self.set_pyspin_value("AcquisitionFrameRateEnable", True)
            is_success2 = self.set_pyspin_value("AcquisitionFrameRate", value)
            return is_success1 and is_success2

        # Brightness (EV) setting
        if propId == cv2.CAP_PROP_BRIGHTNESS:
            return self.set_pyspin_value("AutoExposureEVCompensation", value)

        # Gain setting
        if propId == cv2.CAP_PROP_GAIN:
            if value != -1:
                # Manual
                is_success1 = self.set_pyspin_value("GainAuto", "Off")
                is_success2 = self.set_pyspin_value("Gain", value)
                return is_success1 and is_success2
            else:
                # Auto
                return self.set_pyspin_value("GainAuto", "Continuous")

        # Exposure setting
        if propId == cv2.CAP_PROP_EXPOSURE:
            if value != -1:
                # Manual
                is_success1 = self.set_pyspin_value("ExposureAuto", "Off")
                is_success2 = self.set_pyspin_value("ExposureTime", value)
                return is_success1 and is_success2
            else:
                # Auto
                return self.set_pyspin_value("ExposureAuto", "Continuous")

        # Gamma setting
        if propId == cv2.CAP_PROP_GAMMA:
            is_success1 = self.set_pyspin_value("GammaEnable", True)
            is_success2 = self.set_pyspin_value("Gamma", value)
            return is_success1 and is_success2

        # Trigger Mode setting
        if propId == cv2.CAP_PROP_TRIGGER:
            if type(value) is not bool:
                warn(f"'value' must be 'bool', not '{type(value).__name__}'")
                return False

            trigger_mode = "On" if value else "Off"
            return self.set_pyspin_value("TriggerMode", trigger_mode)

        # TriggerDelay setting
        if propId == cv2.CAP_PROP_TRIGGER_DELAY:
            return self.set_pyspin_value("TriggerDelay", value)

        # BackLigth setting
        if propId == cv2.CAP_PROP_BACKLIGHT:
            if type(value) is not bool:
                warn(f"'value' must be 'bool', not '{type(value).__name__}'")
                return False

            device_indicato_mode = "Active" if value else "Inactive"
            return self.set_pyspin_value("DeviceIndicatorMode", device_indicato_mode)

        # Auto White Balance setting
        if propId == cv2.CAP_PROP_AUTO_WB:
            if type(value) is not bool:
                warn(f"'value' must be 'bool', not '{type(value).__name__}'")
                return False

            balance_white_auto_mode = "Continuous" if value else "Off"
            return self.set_pyspin_value("BalanceWhiteAuto", balance_white_auto_mode)

        # If none of the above conditions apply
        warn(f"propID={propId} is not supported")

        return False

    def get(self, propId: "cv2.VideoCaptureProperties") -> any:
        """
        Returns the specified VideoCapture property.

        Parameters
        ----------
        propId_id : cv2.VideoCaptureProperties
            Property identifier from cv2.VideoCaptureProperties

        Returns
        -------
        value : any
           Value for the specified property. Value Flase is returned when querying a property that is not supported.
        """
        # Width
        if propId == cv2.CAP_PROP_FRAME_WIDTH:
            return self.get_pyspin_value("Width")

        # Height
        if propId == cv2.CAP_PROP_FRAME_HEIGHT:
            return self.get_pyspin_value("Height")

        # Frame Rate
        if propId == cv2.CAP_PROP_FPS:
            # If this does not equal the AcquisitionFrameRate
            # it is because the ExposureTime is greater than the frame time.
            return self.get_pyspin_value("ResultingFrameRate")

        # Brightness
        if propId == cv2.CAP_PROP_BRIGHTNESS:
            return self.get_pyspin_value("AutoExposureEVCompensation")

        # Gain
        if propId == cv2.CAP_PROP_GAIN:
            return self.get_pyspin_value("Gain")

        # Exposure Time
        if propId == cv2.CAP_PROP_EXPOSURE:
            return self.get_pyspin_value("ExposureTime")

        # Gamma
        if propId == cv2.CAP_PROP_GAMMA:
            return self.get_pyspin_value("Gamma")

        # Temperature
        if propId == cv2.CAP_PROP_TEMPERATURE:
            return self.get_pyspin_value("DeviceTemperature")

        # Trigger Mode
        if propId == cv2.CAP_PROP_TRIGGER:
            trigger_mode = self.get_pyspin_value("TriggerMode")
            if trigger_mode == PySpin.TriggerMode_Off:
                return False
            elif trigger_mode == PySpin.TriggerMode_On:
                return True
            else:
                return trigger_mode

        # Trigger Delay
        if propId == cv2.CAP_PROP_TRIGGER_DELAY:
            return self.get_pyspin_value("TriggerDelay")

        # Back Light
        if propId == cv2.CAP_PROP_BACKLIGHT:
            device_indicator_mode = self.get_pyspin_value("DeviceIndicatorMode")
            if device_indicator_mode == PySpin.DeviceIndicatorMode_Inactive:
                return False
            elif device_indicator_mode == PySpin.DeviceIndicatorMode_Active:
                return True
            else:
                return device_indicator_mode

        # Auto White Balance setting
        if propId == cv2.CAP_PROP_AUTO_WB:
            balance_white_auto = self.get_pyspin_value("BalanceWhiteAuto")

            if balance_white_auto == PySpin.BalanceWhiteAuto_Off:
                return False
            elif balance_white_auto == PySpin.BalanceWhiteAuto_Continuous:
                return True
            else:
                return balance_white_auto

        # If none of the above conditions apply
        warn(f"propID={propId} is not supported")

        return False

    def setExceptionMode(self, enable: bool) -> None:
        """Switches exceptions mode.

        Methods raise exceptions if not successful instead of returning an error code.

        Parameters
        ----------
        enable : bool
        """
        if enable:
            warnings.simplefilter("error", EasyPySpinWarning)
        else:
            warnings.simplefilter("ignore", EasyPySpinWarning)

    def set_pyspin_value(self, node_name: str, value: any) -> bool:
        """Setting PySpin value with some useful checks.

        This function adds functions that PySpin's ``SetValue`` does not support,
        such as **writable check**, **argument type check**, **value range check and auto-clipping**.
        If it fails, a warning will be raised. ``EasyPySpinWarning`` can control this warning.

        Parameters
        ----------
        node_name : str
            Name of the node to set.
        value : any
            Value to set. The type is assumed to be ``int``, ``float``, ``bool``, ``str`` or ``PySpin Enumerate``.

        Returns
        -------
        is_success : bool
            Whether success or not: True for success, False for failure.

        Examples
        --------
        Success case.

        >>> set_pyspin_value("ExposureTime", 1000.0)
        True
        >>> set_pyspin_value("Width", 256)
        True
        >>> set_pyspin_value("GammaEnable", False)
        True
        >>> set_pyspin_value("ExposureAuto", PySpin.ExposureAuto_Off)
        True
        >>> set_pyspin_value("ExposureAuto", "Off")
        True

        Success case, and the value is clipped.

        >>> set_pyspin_value("ExposureTime", 0.1)
        EasyPySpinWarning: 'ExposureTime' value must be in the range of [20.0, 30000002.0], so 0.1 become 20.0
        True

        Failure case.

        >>> set_pyspin_value("Width", 256.0123)
        EasyPySpinWarning: 'value' must be 'int', not 'float'
        False
        >>> set_pyspin_value("hoge", 1)
        EasyPySpinWarning: 'CameraPtr' object has no attribute 'hoge'
        False
        >>> set_pyspin_value("ExposureAuto", "hoge")
        EasyPySpinWarning: 'PySpin' object has no attribute 'ExposureAuto_hoge'
        False
        """
        if not self.isOpened():
            warn("Camera is not open")
            return False

        # Check 'CameraPtr' object has attribute 'node_name'
        if not hasattr(self.cam, node_name):
            warn(f"'{type(self.cam).__name__}' object has no attribute '{node_name}'")
            return False

        # Get attribution
        node = getattr(self.cam, node_name)

        # Check 'node' object has attribute 'SetValue'
        if not hasattr(node, "SetValue"):
            warn(f"'{type(node).__name__}' object has no attribute 'SetValue'")
            return False

        # Check node is writable
        if not PySpin.IsWritable(node):
            warn(f"'{node_name}' is not writable")
            return False

        # Get type
        node_type = type(node)
        value_type = type(value)

        # Convert numpy array with one element
        # into a standard Python scalar object
        if value_type is np.ndarray:
            if value.size == 1:
                value = value.item()
                value_type = type(value)

        # Check value type of Integer node case
        if node_type is PySpin.IInteger:
            if value_type is not int:
                warn(f"'value' must be 'int', not '{value_type.__name__}'")
                return False

        # Check value type of Float node case
        elif node_type is PySpin.IFloat:
            if value_type not in (int, float):
                warn(f"'value' must be 'int' or 'float', not '{value_type.__name__}'")
                return False

        # Check value type of Boolean node case
        elif node_type is PySpin.IBoolean:
            if value_type is not bool:
                warn(f"'value' must be 'bool', not '{value_type.__name__}'")
                return False

        # Check value type of Enumeration node case
        elif isinstance(node, PySpin.IEnumeration):
            if value_type is str:
                # If the type is ``str``,
                # replace the corresponding PySpin's Enumeration if it exists.
                enumeration_name = f"{node_name}_{value}"
                if hasattr(PySpin, enumeration_name):
                    value = getattr(PySpin, enumeration_name)
                    value_type = type(value)
                else:
                    warn(f"'PySpin' object has no attribute '{enumeration_name}'")
                    return False
            elif value_type is not int:
                warn(
                    f"'value' must be PySpin's Enumeration, not '{value_type.__name__}'"
                )
                return False

        # Clip the value when node type is Integer of Float
        if node_type in (PySpin.IInteger, PySpin.IFloat):
            v_min = node.GetMin()
            v_max = node.GetMax()
            value_clipped = min(max(value, v_min), v_max)
            if value_clipped != value:
                warn(
                    f"'{node_name}' value must be in the range of [{v_min}, {v_max}], so {value} become {value_clipped}"
                )
                value = value_clipped

        # Finally, SetValue
        try:
            node.SetValue(value)
        except PySpin.SpinnakerException as e:
            msg_pyspin = str(e)
            warn(msg_pyspin)
            return False

        return True

    def get_pyspin_value(self, node_name: str) -> any:
        """Getting PySpin value with some useful checks.

        Parameters
        ----------
        node_name : str
            Name of the node to get.

        Returns
        -------
        value : any
            value

        Examples
        --------
        Success case.

        >>> get_pyspin_value("ExposureTime")
        103.0
        >>> get_pyspin_value("GammaEnable")
        True
        >>> get_pyspin_value("ExposureAuto")
        0

        Failure case.

        >>> get_pyspin_value("hoge")
        EasyPySpinWarning: 'CameraPtr' object has no attribute 'hoge'
        None
        """
        if not self.isOpened():
            warn("Camera is not open")
            return False

        # Check 'CameraPtr' object has attribute 'node_name'
        if not hasattr(self.cam, node_name):
            warn(f"'{type(self.cam).__name__}' object has no attribute '{node_name}'")
            return None

        # Get attribution
        node = getattr(self.cam, node_name)

        # Check 'node_name' object has attribute 'GetValue'
        if not hasattr(node, "GetValue"):
            warn(f"'{type(node).__name__}' object has no attribute 'GetValue'")
            return None

        # Check node is readable
        if not PySpin.IsReadable(node):
            warn(f"'{node_name}' is not readable")
            return None

        # Finally, GetValue
        value = node.GetValue()

        return value

    def _get_camera_series_name(self) -> str:
        """Get camera series name"""
        model_name = self.get_pyspin_value("DeviceModelName")

        series_names = ["BFS", "BFLY", "CM3", "FL3", "GS3", "ORX", "FFY-DL"]
        for name in series_names:
            if name in model_name:
                return name

    def _configure_as_primary(self):
        """Configure as primary camera for synchronized capture

        Notes
        -----
        https://www.flir.com/support-center/iis/machine-vision/application-note/configuring-synchronized-capture-with-multiple-cameras/

        4. Set the output line
            1. For CM3, FL3, GS3, FFY-DL, and ORX cameras, select Line2 from the Line Selection dropdown and set Line Mode to Output.
            2. For BFS cameras, select Line1 from the Line Selection dropdown and set Line Mode to Output.
        5. For BFS and BFLY cameras enable the 3.3V line
            1. For BFS cameras from the line selection drop-down select Line2 and check the checkbox for 3.3V Enable.
            2. For BFLY cameras, set 3.3V Enable to true
        """
        series_name = self._get_camera_series_name()

        # Set the output line
        if series_name in ["CM3", "FL3", "GS3", "FFY-DL", "ORX"]:
            # For CM3, FL3, GS3, FFY-DL, and ORX cameras,
            # select Line2 from the Line Selection dropdown and set Line Mode to Output.
            self.set_pyspin_value("LineSelector", "Line2")
            self.set_pyspin_value("LineMode", "Output")
        elif series_name in ["BFS"]:
            # For BFS cameras, select Line1 from the Line Selection dropdown
            # and set Line Mode to Output.
            self.set_pyspin_value("LineSelector", "Line1")
            self.set_pyspin_value("LineMode", "Output")

        # For BFS and BFLY cameras enable the 3.3V line
        if series_name in ["BFS"]:
            # For BFS cameras from the line selection drop-down select Line2
            # and check the checkbox for 3.3V Enable.
            self.set_pyspin_value("LineSelector", "Line2")
            self.set_pyspin_value("V3_3Enable", True)
        elif series_name in ["BFLY"]:
            # For BFLY cameras, set 3.3V Enable to true
            self.set_pyspin_value("V3_3Enable", True)

    def _configure_as_secondary(self):
        """Configure as secondary camera for synchronized capture

        Notes
        -----
        https://www.flir.com/support-center/iis/machine-vision/application-note/configuring-synchronized-capture-with-multiple-cameras/

        2. Select the GPIO tab.
            1. Set the trigger source
            2. For BFS, CM3, FL3, FFY-DL, and GS3 cameras, from the Trigger Source drop-down, select Line 3.
            3. For ORX cameras, from the Trigger Source drop-down, select Line 5.
            4. For BFLY cameras, from the Trigger Source drop-down, select Line 0
        3. From the Trigger Overlap drop-down, select Read Out.
        4. From the Trigger Mode drop-down, select On.
        """
        series_name = self._get_camera_series_name()

        self.set_pyspin_value("TriggerMode", "Off")
        self.set_pyspin_value("TriggerSelector", "FrameStart")

        # Set the trigger source
        if series_name in ["BFS", "CM3", "FL3", "FFY-DL", "GS3"]:
            # For BFS, CM3, FL3, FFY-DL, and GS3 cameras,
            # from the Trigger Source drop-down, select Line 3.
            self.set_pyspin_value("TriggerSource", "Line3")
        elif series_name in ["ORX"]:
            # For ORX cameras, from the Trigger Source drop-down, select Line 5.
            self.set_pyspin_value("TriggerSource", "Line5")

        # From the Trigger Overlap drop-down, select Read Out.
        self.set_pyspin_value("TriggerOverlap", "ReadOut")

        # From the Trigger Mode drop-down, select On.
        self.set_pyspin_value("TriggerMode", "On")
