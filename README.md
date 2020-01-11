# EasyPySpin

EasyPySpin is an unofficial wrapper for FLIR [Spinnaker SDK](https://www.flir.com/products/spinnaker-sdk/). This wrapper provides much the same way as the OpenCV VideoCapture class.

## Requirement
* PySpin
    * Download Spinnaker SDK from [here](https://www.flir.com/support-center/iis/machine-vision/downloads/spinnaker-sdk-and-firmware-download/).
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

ret, frame = cap.read()

cv2.imwrite("frame.png", frame)
    
cap.release()
```
### Basic property settings
You can access properties using `cap.set(propId, value)` or `cap.get(propId)`. See also [supported propId](#Supported-VideoCaptureProperties).
```python
cap.set(cv2.CAP_PROP_EXPOSURE, 100000) #us
cap.set(cv2.CAP_PROP_GAIN, 10) #dB

print(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
print(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
```

### Advanced property settings
`cap.set()` and `cap.get()` can only access basic properties. To access advanced properties, you should use QuickSpinAPI or GenAPI.
```python
#QuickSpinAPI example
cap.cam.AdcBitDepth.SetValue(PySpin.AdcBitDepth_Bit12)
cap.cam.PixelFormat.SetValue(PySpin.PixelFormat_Mono16)

#GenAPI example
node_exposureAuto = PySpin.CEnumerationPtr(cap.nodemap.GetNode("ExposureAuto"))
exposureAuto = PySpin.CEnumEntryPtr(node_exposureAuto.GetEntryByName("Once")).GetValue()
node_exposureAuto.SetIntValue(exposureAuto)
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

## External Links
* [Spinnaker® SDK Programmer's Guide and API Reference (C++)](http://softwareservices.ptgrey.com/Spinnaker/latest/index.html)
* [Getting Started with Spinnaker SDK on MacOS Applicable products](https://www.flir.com/support-center/iis/machine-vision/application-note/getting-started-with-spinnaker-sdk-on-macos/)
* [Spinnaker Nodes](https://www.flir.com/support-center/iis/machine-vision/application-note/spinnaker-nodes/)
* [Configuring Synchronized Capture with Multiple Cameras](https://www.flir.com/support-center/iis/machine-vision/application-note/configuring-synchronized-capture-with-multiple-cameras)
