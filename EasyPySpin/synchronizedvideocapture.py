import PySpin

class SynchronizedVideoCapture:
    """
    Hardware synchronized video capturing.
    It can be handled in the same way as the "VideoCapture" class and the return value is stored in the list.
    
    You can find instructions on how to connect the camera in FLIR official page.
    [https://www.flir.com/support-center/iis/machine-vision/application-note/configuring-synchronized-capture-with-multiple-cameras]
    
    NOTE : Currently, only two cameras (primary and secondary) are supported, but I would like to support multiple secondary cameras in the future.
    NOTE : I only have the "BFS" camera, so I haven't tested it with any other camera ("BFLY", "CM3", etc...). So, if you have a problem, please send me an issue or PR.
    """
    def __init__(self, cap_primary, cap_secondary):
        self.cap_primary = cap_primary
        self.cap_secondary = cap_secondary

        self.cap_primary = self._configure_as_primary(self.cap_primary)
        self.cap_secondary = self._configure_as_secondary(self.cap_secondary)

        self.cap_primary.auto_software_trigger_execute = True
        
    def __del__(self):
        self.cap_primary.release()
        self.cap_secondary.release()

    def release(self):
        self.__del__()

    def isOpened(self):
        return [self.cap_primary.isOpened(), self.cap_secondary.isOpened()]
    
    def read(self):
        if not self.cap_primary.cam.IsStreaming():
            self.cap_primary.cam.BeginAcquisition()
        
        if not self.cap_secondary.cam.IsStreaming():
            self.cap_secondary.cam.BeginAcquisition()

        if (self.cap_primary.cam.TriggerMode.GetValue()==PySpin.TriggerMode_On and 
            self.cap_primary.cam.TriggerSource.GetValue()==PySpin.TriggerSource_Software and 
            self.cap_primary.auto_software_trigger_execute==True):
            self.cap_primary.cam.TriggerSoftware.Execute()

        ret_p, frame_p = self.cap_primary.read()
        ret_s, frame_s = self.cap_secondary.read()
        ret = [ret_p, ret_s]
        frame = [frame_p, frame_s]
        return ret, frame

    def set(self, propId, value):
        ret_p = self.cap_primary.set(propId, value)
        ret_s = self.cap_secondary.set(propId, value)
        return [ret_p, ret_s]

    def get(self, propId):
        value_p = self.cap_primary.get(propId)
        value_s = self.cap_secondary.get(propId)
        return [value_p, value_s]

    def _configure_as_primary(self, cap):
        series_name = self._which_camera_series(cap)
        
        # Set the output line
        if series_name in ["CM3", "FL3", "GS3", "FFY-DL", "ORX"]:
            # For CM3, FL3, GS3, FFY-DL, and ORX cameras, 
            # select Line2 from the Line Selection dropdown and set Line Mode to Output.
            cap.cam.LineSelector.SetValue(PySpin.LineSelector_Line2)
            cap.cam.LineMode.SetValue(PySpin.LineMode_Output)
        elif series_name in ["BFS"]:
            # For BFS cameras, select Line1 from the Line Selection dropdown 
            # and set Line Mode to Output.
            cap.cam.LineSelector.SetValue(PySpin.LineSelector_Line1)
            cap.cam.LineMode.SetValue(PySpin.LineMode_Output)

        # For BFS and BFLY cameras enable the 3.3V line
        if series_name in ["BFS"]:
            # For BFS cameras from the line selection drop-down select Line2 
            # and check the checkbox for 3.3V Enable.
            cap.cam.LineSelector.SetValue(PySpin.LineSelector_Line2)
            cap.cam.V3_3Enable.SetValue(True)
        elif series_name in ["BFLY"]:
            # For BFLY cameras, set 3.3V Enable to true
            cap.cam.V3_3Enable.SetValue(True)

        return cap

    def _configure_as_secondary(self, cap):
        series_name = self._which_camera_series(cap)
        
        cap.cam.TriggerMode.SetValue(PySpin.TriggerMode_Off)
        cap.cam.TriggerSelector.SetValue(PySpin.TriggerSelector_FrameStart)
        
        # Set the trigger source
        if series_name in ["BFS", "CM3", "FL3", "FFY-DL", "GS3"]:
            # For BFS, CM3, FL3, FFY-DL, and GS3 cameras, 
            # from the Trigger Source drop-down, select Line 3.
            cap.cam.TriggerSource.SetValue(PySpin.TriggerSource_Line3)
        elif series_name in ["ORX"]:
            # For ORX cameras, from the Trigger Source drop-down, select Line 5.
            cap.cam.TriggerSource.SetValue(PySpin.TriggerSource_Line5)
            
        # From the Trigger Overlap drop-down, select Read Out.
        cap.cam.TriggerOverlap.SetValue(PySpin.TriggerOverlap_ReadOut)

        # From the Trigger Mode drop-down, select On.
        cap.cam.TriggerMode.SetValue(PySpin.TriggerMode_On)

        return cap

    def _which_camera_series(self, cap):
        model_name = cap.cam.DeviceModelName.GetValue()

        series_names = ["BFS", "BFLY", "CM3", "FL3", "GS3", "ORX", "FFY-DL"]
        for name in series_names:
            if name in model_name:
                return name
        return None
