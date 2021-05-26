import warnings
from typing import Union, Tuple

import numpy as np
import cv2
import PySpin

from .utils import EasyPySpinWarning, warn

class VideoCapture:
    """
    Open a FLIR camera for video capturing.

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
        # Check for 'index' type
        if isinstance(index, (int, str))==False:
            raise TypeError("Argument 'index' is required to be an integer or a string")

        # Cerate system instance and get camera list 
        self._system = PySpin.System.GetInstance()
        self._cam_list = self._system.GetCameras()
        num_cam = self._cam_list.GetSize()

        # Check for available cameras
        if num_cam==0:
            print("EasyPySpin: no camera is available", file=stderr)
            self._cam_list.Clear()
            self._system.ReleaseInstance()
            return None
        
        # Try to connect camera
        try:
            # Index case
            if type(index) is int:
                # Check for 'index' bound
                if index<0 or num_cam-1<index:
                    print(f"EasyPySpin: out device of bound (0-{num_cam-1}): {index}", file=stderr)
                self.cam = self._cam_list.GetByIndex(index)
            # Serial case
            elif type(index) is str:
                self.cam = self._cam_list.GetBySerial(index)
        except:
            print("EasyPySpin: camera failed to properly initialize!", file=stderr)
            self._cam_list.Clear()
            self._system.ReleaseInstance()
            return None

        self.cam.Init()
        self.nodemap = self.cam.GetNodeMap()
        
        s_node_map = self.cam.GetTLStreamNodeMap()
        handling_mode = PySpin.CEnumerationPtr(s_node_map.GetNode('StreamBufferHandlingMode'))
        handling_mode_entry = handling_mode.GetEntryByName('NewestOnly')
        handling_mode.SetIntValue(handling_mode_entry.GetValue())

        self.grabTimeout = PySpin.EVENT_TIMEOUT_INFINITE
        self.streamID = 0
        self.auto_software_trigger_execute = False
        
    def __del__(self):
        try:
            if self.cam.IsStreaming():
                self.cam.EndAcquisition()
            self.cam.DeInit()
            del self.cam
            self._cam_list.Clear()
            self._system.ReleaseInstance()
        except: pass

    def release(self):
        """
        Closes capturing device. The method call VideoCapture destructor.
        """
        self.__del__()

    def isOpened(self):
        """
        Returns true if video capturing has been initialized already.
        """
        try: return self.cam.IsValid()
        except: return False

    def read(self):
        """
        returns the next frame.
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
        
        # Execute a software trigger if necessary 
        if (self.cam.TriggerMode.GetValue()  ==PySpin.TriggerMode_On and 
            self.cam.TriggerSource.GetValue()==PySpin.TriggerSource_Software and 
            self.auto_software_trigger_execute==True):
        # Execute a software trigger if required
        if (PySpin.IsAvailable(self.cam.TriggerSoftware) 
                and self.auto_software_trigger_execute):
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

        image = self.cam.GetNextImage(self.grabTimeout, self.streamID)
        if image.IsIncomplete():
            return False, None
        
        img_NDArray = image.GetNDArray()
        image.Release()
        return True, img_NDArray
    
        """
    
    def set(self, propId: 'cv2.VideoCaptureProperties', value: any) -> bool:
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
            return (is_success1 and is_success2)

        # Brightness (EV) setting
        if propId == cv2.CAP_PROP_BRIGHTNESS:
            return self.set_pyspin_value("AutoExposureEVCompensation", value)
        
        # Gain setting
        if propId == cv2.CAP_PROP_GAIN:
            if value != -1:
                # Manual
                is_success1 = self.set_pyspin_value("GainAuto", "Off")
                is_success2 = self.set_pyspin_value("Gain", value)
                return (is_success1 and is_success2)
            else:
                # Auto
                return self.set_pyspin_value("GainAuto", "Continuous")
        
        # Exposure setting
        if propId == cv2.CAP_PROP_EXPOSURE:
            if value != -1:
                # Manual
                is_success1 = self.set_pyspin_value("ExposureAuto", "Off")
                is_success2 = self.set_pyspin_value("ExposureTime", value)
                return (is_success1 and is_success2)
            else:
                # Auto
                return self.set_pyspin_value("ExposureAuto", "Continuous")
        
        # Gamma setting
        if propId == cv2.CAP_PROP_GAMMA:
            is_success1 = self.set_pyspin_value("GammaEnable", True)
            is_success2 = self.set_pyspin_value("Gamma", value)
            return (is_success1 and is_success2)

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
    
    def get(self, propId: 'cv2.VideoCaptureProperties') -> any:
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
            warnings.simplefilter('error', EasyPySpinWarning)
        else:
            warnings.simplefilter('ignore', EasyPySpinWarning)

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
        node_type  = type(node)
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
                warn(f"'value' must be PySpin's Enumeration, not '{value_type.__name__}'")
                return False
        
        # Clip the value when node type is Integer of Float
        if node_type in (PySpin.IInteger, PySpin.IFloat):
            v_min = node.GetMin()
            v_max = node.GetMax()
            value_clipped = min(max(value, v_min), v_max)
            if value_clipped != value:
                warn(f"'{node_name}' value must be in the range of [{v_min}, {v_max}], so {value} become {value_clipped}")
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
