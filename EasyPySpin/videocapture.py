import warnings
import cv2
import PySpin
from sys import stderr

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

        Returns
        -------
        retval : bool
            false if no frames has been grabbed.
        image : array_like 
            grabbed image is returned here. If no image has been grabbed the image will be None.
        """
        if not self.cam.IsStreaming():
            self.cam.BeginAcquisition()
        
        # Execute a software trigger if necessary 
        if (self.cam.TriggerMode.GetValue()  ==PySpin.TriggerMode_On and 
            self.cam.TriggerSource.GetValue()==PySpin.TriggerSource_Software and 
            self.auto_software_trigger_execute==True):
            self.cam.TriggerSoftware.Execute()

        image = self.cam.GetNextImage(self.grabTimeout, self.streamID)
        if image.IsIncomplete():
            return False, None
        
        img_NDArray = image.GetNDArray()
        image.Release()
        return True, img_NDArray
    
    def set(self, propId, value):
        """
        Sets a property in the VideoCapture.

        Parameters
        ----------
        propId_id : cv2.VideoCaptureProperties
            Property identifier from cv2.VideoCaptureProperties
        value : int or float or bool
            Value of the property.
        
        Returns
        -------
        retval : bool
           True if property setting success.
        """
        #Exposure setting
        if propId==cv2.CAP_PROP_EXPOSURE:
            #Auto
            if value<0: return self._set_ExposureAuto(PySpin.ExposureAuto_Continuous)

            #Manual
            ret = self._set_ExposureAuto(PySpin.ExposureAuto_Off)
            if ret==False: return False
            return self._set_ExposureTime(value)
        
        #Gain setting
        if propId==cv2.CAP_PROP_GAIN:
            #Auto
            if value<0: return self._set_GainAuto(PySpin.GainAuto_Continuous)
            
            #Manual
            ret = self._set_GainAuto(PySpin.GainAuto_Off)
            if ret==False: return False
            return self._set_Gain(value)

        #Brightness(EV) setting
        if propId==cv2.CAP_PROP_BRIGHTNESS:
            return self._set_Brightness(value)
        
        #Gamma setting
        if propId==cv2.CAP_PROP_GAMMA:
            return self._set_Gamma(value)

        #FrameRate setting
        if propId==cv2.CAP_PROP_FPS:
            return self._set_FrameRate(value)

        #BackLigth setting
        if propId==cv2.CAP_PROP_BACKLIGHT:
            return self._set_BackLight(value)
        
        #Trigger Mode setting (ON/OFF)
        if propId==cv2.CAP_PROP_TRIGGER:
            return self._set_Trigger(value)

        #TriggerDelay setting
        if propId==cv2.CAP_PROP_TRIGGER_DELAY:
            return self._set_TriggerDelay(value)

        return False
    
    def get(self, propId):
        """
        Returns the specified VideoCapture property.
        
        Parameters
        ----------
        propId_id : cv2.VideoCaptureProperties
            Property identifier from cv2.VideoCaptureProperties
        
        Returns
        -------
        value : int or float or bool
           Value for the specified property. Value Flase is returned when querying a property that is not supported.
        """
        if propId==cv2.CAP_PROP_EXPOSURE:
            return self._get_ExposureTime()

        if propId==cv2.CAP_PROP_GAIN:
            return self._get_Gain()

        if propId==cv2.CAP_PROP_BRIGHTNESS:
            return self._get_Brightness()

        if propId==cv2.CAP_PROP_GAMMA:
            return self._get_Gamma()

        if propId==cv2.CAP_PROP_FRAME_WIDTH:
            return self._get_Width()

        if propId==cv2.CAP_PROP_FRAME_HEIGHT:
            return self._get_Height()

        if propId==cv2.CAP_PROP_FPS:
            return self._get_FrameRate()

        if propId==cv2.CAP_PROP_TEMPERATURE:
            return self._get_Temperature()

        if propId==cv2.CAP_PROP_BACKLIGHT:
            return self._get_BackLight()

        if propId==cv2.CAP_PROP_TRIGGER:
            return self._get_Trigger()

        if propId==cv2.CAP_PROP_TRIGGER_DELAY:
            return self._get_TriggerDelay()

        return False
    
    def __clip(self, a, a_min, a_max):
        return min(max(a, a_min), a_max)
    
    def _set_ExposureTime(self, value):
        if not type(value) in (int, float): return False
        exposureTime_to_set = self.__clip(value, self.cam.ExposureTime.GetMin(), self.cam.ExposureTime.GetMax())
        self.cam.ExposureTime.SetValue(exposureTime_to_set)
        return True

    def _set_ExposureAuto(self, value):
        self.cam.ExposureAuto.SetValue(value)
        return True

    def _set_Gain(self, value):
        if not type(value) in (int, float): return False
        gain_to_set = self.__clip(value, self.cam.Gain.GetMin(), self.cam.Gain.GetMax())
        self.cam.Gain.SetValue(gain_to_set)
        return True
    def setExceptionMode(self, enable: bool) -> None:
        """Switches exceptions mode.

    def _set_GainAuto(self, value):
        self.cam.GainAuto.SetValue(value)
        return True
    
    def _set_Brightness(self, value):
        if not type(value) in (int, float): return False
        brightness_to_set = self.__clip(value, self.cam.AutoExposureEVCompensation.GetMin(), self.cam.AutoExposureEVCompensation.GetMax())
        self.cam.AutoExposureEVCompensation.SetValue(brightness_to_set)
        return True
        Methods raise exceptions if not successful instead of returning an error code.

    def _set_Gamma(self, value):
        if not type(value) in (int, float): return False
        gamma_to_set = self.__clip(value, self.cam.Gamma.GetMin(), self.cam.Gamma.GetMax())
        self.cam.Gamma.SetValue(gamma_to_set)
        return True
        Parameters
        ----------
        enable : bool
        """
        if enable:
            warnings.simplefilter('error', EasyPySpinWarning)
        else:
            warnings.simplefilter('ignore', EasyPySpinWarning)

    def _set_FrameRate(self, value):
        if not type(value) in (int, float): return False
        self.cam.AcquisitionFrameRateEnable.SetValue(True)
        fps_to_set = self.__clip(value, self.cam.AcquisitionFrameRate.GetMin(), self.cam.AcquisitionFrameRate.GetMax())
        self.cam.AcquisitionFrameRate.SetValue(fps_to_set)
        return True
    def set_pyspin_value(self, node_name: str, value: any) -> bool:
        """Setting PySpin value with some useful checks.

    def _set_BackLight(self, value):
        if value==True:backlight_to_set = PySpin.DeviceIndicatorMode_Active
        elif value==False: backlight_to_set = PySpin.DeviceIndicatorMode_Inactive
        else: return False
        self.cam.DeviceIndicatorMode.SetValue(backlight_to_set)
        return True
        This function adds functions that PySpin's ``SetValue`` does not support,
        such as **writable check**, **argument type check**, **value range check and auto-clipping**.
        If it fails, a warning will be raised. ``EasyPySpinWarning`` can control this warning.
        
        Parameters
        ----------
        node_name : str
            Name of the node to set.
        value : any
            Value to set. The type is assumed to be ``int``, ``float``, ``bool``, ``str`` or ``PySpin Enumerate``.

    def _set_Trigger(self, value):
        if value==True:
            trigger_mode_to_set = PySpin.TriggerMode_On
        elif value==False:
            trigger_mode_to_set = PySpin.TriggerMode_Off
        else:
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

        self.cam.TriggerMode.SetValue(trigger_mode_to_set)
        return True

    def _set_TriggerDelay(self, value):
        if not type(value) in (int, float): return False
        delay_to_set = self.__clip(value, self.cam.TriggerDelay.GetMin(), self.cam.TriggerDelay.GetMax())
        self.cam.TriggerDelay.SetValue(delay_to_set)
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

    def _get_ExposureTime(self):
        return self.cam.ExposureTime.GetValue()

    def _get_Gain(self):
        return self.cam.Gain.GetValue()

    def _get_Brightness(self):
        return self.cam.AutoExposureEVCompensation.GetValue()

    def _get_Gamma(self):
        return self.cam.Gamma.GetValue()

    def _get_Width(self):
        return self.cam.Width.GetValue()

    def _get_Height(self):
        return self.cam.Height.GetValue()

    def _get_FrameRate(self):
        return self.cam.AcquisitionFrameRate.GetValue()

    def _get_Temperature(self):
        return self.cam.DeviceTemperature.GetValue()

    def _get_BackLight(self):
        status = self.cam.DeviceIndicatorMode.GetValue()
        return (True  if status == PySpin.DeviceIndicatorMode_Active else
                False if status == PySpin.DeviceIndicatorMode_Inactive else
                status)
    
    def _get_Trigger(self):
        status = self.cam.TriggerMode.GetValue()
        return (True  if status == PySpin.TriggerMode_On else
                False if status == PySpin.TriggerMode_Off else
                status)

    def _get_TriggerDelay(self):
        return self.cam.TriggerDelay.GetValue()
