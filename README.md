# EasyPySpin

EasyPySpin is an unofficial wrapper for FLIR [Spinnaker SDK](https://www.flir.com/products/spinnaker-sdk/). This wrapper provides much the same way as the OpenCV VideoCapture class.

## Requirement
* [PySpin](https://www.flir.com/support-center/iis/machine-vision/downloads/spinnaker-sdk-and-firmware-download/)
* OpenCV

## Run on command line
Live streaming will start when `EasyPySpin.py` is executed.
```
python EasyPySpin.py
```

## Use as a module
`EasyPySpin.py` can be used as a module.
### Capture image from camera
Here's an example to capture image from camera. 
```python
import cv2
import EasyPySpin

cap = EasyPySpin.VideoCapture(0)

cap.set(cv2.CAP_PROP_EXPOSURE, 100000) #us
cap.set(cv2.CAP_PROP_GAIN, 10) #dB

ret, frame = cap.read()

cv2.imwrite("frame.png", frame)
    
cap.release()
```
### Accessing properties
You can access properties using `cap.set(propId, value)` or `cap.get(propId)`.
```python
cap.set(cv2.CAP_PROP_GAMMA, 1.0)
cap.set(cv2.CAP_PROP_FPS, 30)

print(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
print(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
```

### Advanced properties
`cap.set()` and `cap.get()` can only access simple properties. To access advanced properties, you should use GenAPI or QuickSpinAPI.
```python
#QuickSpinAPI example
cap.cam.AdcBitDepth.SetValue(PySpin.AdcBitDepth_Bit12)
cap.cam.PixelFormat.SetValue(PySpin.PixelFormat_Mono16)

#GenAPI example

```

## Supported VideoCaptureProperties
* `cv2.CAP_PROP_EXPOSURE`
* `cv2.CAP_PROP_GAIN`
* `cv2.CAP_PROP_GAMMA`
* `cv2.CAP_PROP_FPS`
* `cv2.CAP_PROP_BRIGHTNESS` 
* `cv2.CAP_PROP_FRAME_WIDTH` (get only)
* `cv2.CAP_PROP_FRAME_HEIGHT` (get only)
* `cv2.CAP_PROP_TEMPERATURE` (get only)
* `cv2.CAP_PROP_BACKLIGHT`
