import cv2
import PySpin

class VideoCapture:
    def __init__(self, index):
        self.system = PySpin.System.GetInstance()
        self.cam_list = self.system.GetCameras()
        #num_cam = self.cam_list.GetSize()
        try: self.cam = self.cam_list.GetByIndex(index)
        except: return None
        self.cam.Init()
        self.nodemap = self.cam.GetNodeMap()

        s_node_map = self.cam.GetTLStreamNodeMap()
        handling_mode = PySpin.CEnumerationPtr(s_node_map.GetNode('StreamBufferHandlingMode'))
        handling_mode_entry = handling_mode.GetEntryByName('NewestOnly')
        handling_mode.SetIntValue(handling_mode_entry.GetValue())

        self.cam.BeginAcquisition()

    def __del__(self):
        try:
            self.cam.EndAcquisition()
            self.cam.DeInit()
            del self.cam
            self.cam_list.Clear()
            self.system.ReleaseInstance()
        except: pass

    def release(self):
        self.__del__()

    def isOpened(self):
        try: return self.cam.IsValid()
        except: return False

    def read(self):
        image = self.cam.GetNextImage()
        if image.IsIncomplete():
            return False, None
        
        img_NDArray = image.GetNDArray()
        image.Release()
        return True, img_NDArray
    
    def set(self, propId, value):
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
        
        #Gamma setting
        if propId==cv2.CAP_PROP_GAMMA:
            return self._set_Gamma(value)

        #FrameRate setting
        if propId==cv2.CAP_PROP_FPS:
            return self._set_FrameRate(value)

        return False
    
    def get(self, propId):
        if propId==cv2.CAP_PROP_EXPOSURE:
            return self._get_ExposureTime()

        if propId==cv2.CAP_PROP_GAIN:
            return self._get_Gain()

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

    def _set_GainAuto(self, value):
        self.cam.GainAuto.SetValue(value)
        return True

    def _set_Gamma(self, value):
        if not type(value) in (int, float): return False
        gamma_to_set = self.__clip(value, self.cam.Gamma.GetMin(), self.cam.Gamma.GetMax())
        self.cam.Gamma.SetValue(gamma_to_set)
        return True

    def _set_FrameRate(self, value):
        if not type(value) in (int, float): return False
        self.cam.AcquisitionFrameRateEnable.SetValue(True)
        fps_to_set = self.__clip(value, self.cam.AcquisitionFrameRate.GetMin(), self.cam.AcquisitionFrameRate.GetMax())
        self.cam.AcquisitionFrameRate.SetValue(fps_to_set)
        return True

    def _get_ExposureTime(self):
        return self.cam.ExposureTime.GetValue()

    def _get_Gain(self):
        return self.cam.Gain.GetValue()

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

def main():
    cap = VideoCapture(0)

    if not cap.isOpened():
        print("cap cant open\nexit")
        return -1

    cap.set(cv2.CAP_PROP_EXPOSURE, -1) #-1 sets exposure_time to auto
    cap.set(cv2.CAP_PROP_GAIN, -1) #-1 sets gain to auto
    cap.set(cv2.CAP_PROP_GAMMA, 1)
    cap.set(cv2.CAP_PROP_FPS, 30)


    while True:
        ret, frame = cap.read()

        exposureTime = cap.get(cv2.CAP_PROP_EXPOSURE)
        gain = cap.get(cv2.CAP_PROP_GAIN)
        gamma = cap.get(cv2.CAP_PROP_GAMMA)
        print("exposureTime:", exposureTime)
        print("gain        :", gain)
        print("\033[2A",end="")
        
        img_show = cv2.resize(frame, None, fx=0.25, fy=0.25)
        cv2.imshow("capture", img_show)
        key = cv2.waitKey(30)
        if key==ord("q"):
            break
    
    cv2.destroyAllWindows()
    cap.release()

if __name__=="__main__":
    main()
    
