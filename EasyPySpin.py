import cv2
import PySpin

class VideoCapture:
    def __init__(self, index):
        self.system = PySpin.System.GetInstance()
        self.cam_list = self.system.GetCameras()
        #num_cam = self.cam_list.GetSize()
        try:
            if type(index) is int:
                self.cam = self.cam_list.GetByIndex(index)
            else:
                self.cam = self.cam_list.GetBySerial(index)
        except:
            print("camera failed to properly initialize!")
            return None

        self.cam.Init()
        self.nodemap = self.cam.GetNodeMap()
        
        s_node_map = self.cam.GetTLStreamNodeMap()
        handling_mode = PySpin.CEnumerationPtr(s_node_map.GetNode('StreamBufferHandlingMode'))
        handling_mode_entry = handling_mode.GetEntryByName('NewestOnly')
        handling_mode.SetIntValue(handling_mode_entry.GetValue())
        
    def __del__(self):
        try:
            if self.cam.IsStreaming():
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
        if not self.cam.IsStreaming():
            self.cam.BeginAcquisition()

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

        return False
    
    def get(self, propId):
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
    
    def _set_Brightness(self, value):
        if not type(value) in (int, float): return False
        brightness_to_set = self.__clip(value, self.cam.AutoExposureEVCompensation.GetMin(), self.cam.AutoExposureEVCompensation.GetMax())
        self.cam.AutoExposureEVCompensation.SetValue(brightness_to_set)
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

    def _set_BackLight(self, value):
        if value==True:backlight_to_set = PySpin.DeviceIndicatorMode_Active
        elif value==False: backlight_to_set = PySpin.DeviceIndicatorMode_Inactive
        else: return False
        self.cam.DeviceIndicatorMode.SetValue(backlight_to_set)
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

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--index", type=int, default=0, help="Camera index (Default: 0)")
    parser.add_argument("-e", "--exposure",type=float, default=-1, help="Exposure time [us] (Default: Auto)")
    parser.add_argument("-g", "--gain", type=float, default=-1, help="Gain [dB] (Default: Auto)")
    parser.add_argument("-G", "--gamma", type=float, help="Gamma value")
    parser.add_argument("-b", "--brightness", type=float, help="Brightness [EV]")
    parser.add_argument("-f", "--fps", type=float, help="FrameRate [fps]")
    parser.add_argument("-s", "--scale", type=float, default=0.25, help="Image scale to show (>0) (Default: 0.25)")
    args = parser.parse_args()

    cap = VideoCapture(args.index)

    if not cap.isOpened():
        print("Camera can't open\nexit")
        return -1
    
    cap.set(cv2.CAP_PROP_EXPOSURE, args.exposure) #-1 sets exposure_time to auto
    cap.set(cv2.CAP_PROP_GAIN, args.gain) #-1 sets gain to auto
    if args.gamma      is not None: cap.set(cv2.CAP_PROP_GAMMA, args.gamma)
    if args.fps        is not None: cap.set(cv2.CAP_PROP_FPS, args.fps)
    if args.brightness is not None: cap.set(cv2.CAP_PROP_BRIGHTNESS, args.brightness)

    while True:
        ret, frame = cap.read()

        exposureTime = cap.get(cv2.CAP_PROP_EXPOSURE)
        gain = cap.get(cv2.CAP_PROP_GAIN)
        print("exposureTime:", exposureTime)
        print("gain        :", gain)
        print("\033[2A",end="")
        
        img_show = cv2.resize(frame, None, fx=args.scale, fy=args.scale)
        cv2.imshow("capture", img_show)
        key = cv2.waitKey(30)
        if key==ord("q"):
            break
        elif key==ord("c"):
            import datetime
            time_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            filepath = time_stamp + ".png"
            cv2.imwrite(filepath, frame)
            print("Export > ", filepath)
    
    cv2.destroyAllWindows()
    cap.release()

if __name__=="__main__":
    main()
