import cv2
import PySpin

class VideoCapture:
    def __init__(self, index):
        self.system = PySpin.System.GetInstance()
        self.cam_list = self.system.GetCameras()
        num_cam = self.cam_list.GetSize()
        try:
            self.cam = self.cam_list.GetByIndex(index)
        except:
            return None
        self.cam.Init()
        self.nodemap = self.cam.GetNodeMap()

        s_node_map = self.cam.GetTLStreamNodeMap()
        handling_mode = PySpin.CEnumerationPtr(s_node_map.GetNode('StreamBufferHandlingMode'))
        handling_mode_entry = handling_mode.GetEntryByName('NewestOnly')
        handling_mode.SetIntValue(handling_mode_entry.GetValue())
        
        self.cam.BeginAcquisition()

    def release(self):
        self.cam.EndAcquisition()
        self.cam.DeInit()
        del self.cam
        self.cam_list.Clear()
        self.system.ReleaseInstance()

    def isOpened(self):
        try:
            return self.cam.IsValid()
        except:
            return False

    def read(self):
        image = self.cam.GetNextImage()
        if image.IsIncomplete():
            return False, None

        img_NDArray = image.GetNDArray()
        image.Release()
        return True, img_NDArray
    
    def set(self, propId, value):
        if propId==cv2.CAP_PROP_EXPOSURE:
            if value<0:
                return self.Set_ExposureAuto(True)

            ret = self.Set_ExposureAuto(False)
            if ret==False:
                return False
            else:
                return self.Set_ExposureTime(value)

        if propId==cv2.CAP_PROP_GAIN:
            if value<0:
                return self.Set_GainAuto(True)
            
            ret = self.Set_GainAuto(False)
            if ret==False:
                return False
            else:
                return self.Set_Gain(value)

        if propId==cv2.CAP_PROP_GAMMA:
            return self.Set_Gamma(value)

        return False
    
    def get(self, propId):
        if propId==cv2.CAP_PROP_EXPOSURE:
            return self.Get_ExposureTime()

        if propId==cv2.CAP_PROP_GAIN:
            return self.Get_Gain()

        if propId==cv2.CAP_PROP_GAMMA:
            return self.Get_Gamma()

        return False
    
    def __clip(self, a, a_min, a_max):
        return min(max(a, a_min), a_max)
    
    def Set_ExposureTime(self, value):
        node_exposureTime = PySpin.CFloatPtr(self.nodemap.GetNode("ExposureTime"))
        if PySpin.IsAvailable(node_exposureTime)==False or PySpin.IsWritable(node_exposureTime)==False: return False
        if not type(value) in (int, float): return False
        exposureTime_to_set = self.__clip(value, node_exposureTime.GetMin(), node_exposureTime.GetMax())
        node_exposureTime.SetValue(exposureTime_to_set)
        return True

    def Set_ExposureAuto(self, value):
        node_exposureAuto = PySpin.CEnumerationPtr(self.nodemap.GetNode("ExposureAuto"))
        if PySpin.IsAvailable(node_exposureAuto)==False or PySpin.IsWritable(node_exposureAuto)==False: return False
        if value==True:
            exposureAuto_name = "Continuous"
        elif value==False:
            exposureAuto_name = "Off"
        else:
            exposureAuto_name = "Once"
        exposureAuto = PySpin.CEnumEntryPtr(node_exposureAuto.GetEntryByName(exposureAuto_name)).GetValue()
        node_exposureAuto.SetIntValue(exposureAuto)
        return True

    def Set_Gain(self, value):
        node_gain = PySpin.CFloatPtr(self.nodemap.GetNode("Gain"))
        if PySpin.IsAvailable(node_gain)==False or PySpin.IsWritable(node_gain)==False: return False
        if not type(value) in (int, float): return False
        gain_to_set = self.__clip(value, node_gain.GetMin(), node_gain.GetMax())
        node_gain.SetValue(gain_to_set)
        return True

    def Set_GainAuto(self, value):
        node_gainAuto = PySpin.CEnumerationPtr(self.nodemap.GetNode("GainAuto"))
        if PySpin.IsAvailable(node_gainAuto)==False or PySpin.IsWritable(node_gainAuto)==False: return False
        if value==True:
            gainAuto_name = "Continuous"
        elif value==False:
            gainAuto_name = "Off"
        else:
            gainAuto_name = "Once"
        gainAuto = PySpin.CEnumEntryPtr(node_gainAuto.GetEntryByName(gainAuto_name)).GetValue()
        node_gainAuto.SetIntValue(gainAuto)
        return True

    def Set_Gamma(self, value):
        node_gamma = PySpin.CFloatPtr(self.nodemap.GetNode("Gamma"))
        if PySpin.IsAvailable(node_gamma)==False or PySpin.IsWritable(node_gamma)==False: return False
        if not type(value) in (int, float): return False
        gamma_to_set = self.__clip(value, node_gamma.GetMin(), node_gamma.GetMax())
        node_gamma.SetValue(gamma_to_set)
        return True
    
    def Get_ExposureTime(self):
        node_exposureTime = PySpin.CFloatPtr(self.nodemap.GetNode("ExposureTime"))
        if PySpin.IsAvailable(node_exposureTime)==False or PySpin.IsReadable(node_exposureTime)==False: return False
        return node_exposureTime.GetValue()

    def Get_Gain(self):
        node_gain = PySpin.CFloatPtr(self.nodemap.GetNode("Gain"))
        if PySpin.IsAvailable(node_gain)==False or PySpin.IsReadable(node_gain)==False: return False
        return node_gain.GetValue()

    def Get_Gamma(self):
        node_gamma = PySpin.CFloatPtr(self.nodemap.GetNode("Gamma"))
        if PySpin.IsAvailable(node_gamma)==False or PySpin.IsReadable(node_gamma)==False: return False
        return node_gamma.GetValue()

def main():
    cap = VideoCapture(0)

    if not cap.isOpened():
        print("cap cant open\nexit")
        return -1

    cap.set(cv2.CAP_PROP_EXPOSURE, -1) #-1 sets exposure_time to auto
    cap.set(cv2.CAP_PROP_GAIN, -1) #-1 sets gain to auto
    cap.set(cv2.CAP_PROP_GAMMA, 1)
   
    while True:
        ret, frame = cap.read()

        exposureTime = cap.get(cv2.CAP_PROP_EXPOSURE)
        gain = cap.get(cv2.CAP_PROP_GAIN)
        print("exposureTime:", exposureTime)
        print("gain        :", gain)
        print("\033[2A",end="")
        
        img_show = cv2.resize(frame, None, fx=0.5, fy=0.5)
        cv2.imshow("capture", img_show)
        key = cv2.waitKey(30)
        if key==ord("q"):
            break
    
    cv2.destroyAllWindows()
    cap.release()

if __name__=="__main__":
    main()
