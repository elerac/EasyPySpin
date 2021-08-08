# EasyPySpin

EasyPySpin is an unofficial wrapper for FLIR [Spinnaker SDK](https://www.flir.com/products/spinnaker-sdk/). This wrapper provides much the same way as the OpenCV VideoCapture class.

## Requirement
* PySpin
    * Download Spinnaker SDK from [here](https://www.flir.com/support-center/iis/machine-vision/downloads/spinnaker-sdk-and-firmware-download/).
* OpenCV

## Installation
```sh
pip install git+https://github.com/elerac/EasyPySpin
```
After installation, connect the camera and try [examples/video.py](examples/video.py).

## Usage
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
cap.set(cv2.CAP_PROP_EXPOSURE, 100000) # us
cap.set(cv2.CAP_PROP_GAIN, 10) # dB

width  = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
```

### Advanced property settings
`cap.set()` and `cap.get()` can only access basic properties. To access advanced properties, you can use QuickSpin API, which PySpin supports.
```python
cap.cam.AdcBitDepth.SetValue(PySpin.AdcBitDepth_Bit12)
cap.cam.PixelFormat.SetValue(PySpin.PixelFormat_Mono16)
```
The other way is to use `cap.set_pyspin_value()` or `cap.get_pyspin_value()`, which are supported by EasyPySpin. These methods check whether the variable is writeable or readable and check the type of the variable, etc., at the same time.
```python
cap.set_pyspin_value("AdcBitDepth", "Bit12")
cap.set_pyspin_value("PixelFormat", "Mono16")

cap.get_pyspin_value("GammaEnable")
cap.get_pyspin_value("DeviceModelName")
```

## Supported VideoCaptureProperties
Here is the list of supported VideoCaptureProperties. 
In `set(propId, value)` and `get(propId)`, PySpin is used to set and get the camera's settings. The relationship between `propId` and PySpin settings is designed to be as close in meaning as possible. The table below shows the relationship between `propId` and PySpin settings in pseudo-code format.

| propId                     | type  | set(propId, value) | value = get(propId) |
| ----                       | ----  | ----        | ----        |
| cv2.CAP_PROP_FRAME_WIDTH   | int   | `Width` = value | value = `Width` |
| cv2.CAP_PROP_FRAME_HEIGHT  | int   | `Height` = value | value = `Height` |
| cv2.CAP_PROP_FPS           | float | `AcquisitionFrameRateEnable` = `True` <br>  `AcquisitionFrameRate` = value | value = `ResultingFrameRate`| 
| cv2.CAP_PROP_BRIGHTNESS    | float | `AutoExposureEVCompensation` = value | value = `AutoExposureEVCompensation` |
| cv2.CAP_PROP_GAIN          | float | if value != -1 <br> &nbsp; `GainAuto` = `Off` <br> &nbsp; `Gain` = value <br> else <br> &nbsp; `GainAuto` = `Continuous` | value = `Gain` |
| cv2.CAP_PROP_EXPOSURE      | float | if value != -1 <br> &nbsp; `ExposureAuto` = `Off` <br> &nbsp; `ExposureTime` = value <br> else <br> &nbsp; `ExposureAuto` = `Continuous` | value = `ExposureTime` |
| cv2.CAP_PROP_GAMMA         | float | `GammaEnable` = `True` <br> `Gamma` = value | value = `Gamma` |
| cv2.CAP_PROP_TEMPERATURE   | float | | value = `DeviceTemperature` |
| cv2.CAP_PROP_TRIGGER       | bool  | if value == `True` <br> &nbsp; `TriggerMode` = `On` <br> else <br> &nbsp; `TriggerMode` = `Off` | if trigger_mode == `On` <br> &nbsp; value = `True` <br> elif trigger_mode == `Off` <br> &nbsp; value = `False` |
| cv2.CAP_PROP_TRIGGER_DELAY | float | `TriggerDelay` = value | value = `TriggerDelay` | 
| cv2.CAP_PROP_BACKLIGHT     | bool  | if value == `True` <br> &nbsp; `DeviceIndicatorMode` = `Active` <br> else <br> &nbsp; `DeviceIndicatorMode` = `Inactive` | if device_indicator_mode == `Active` <br> &nbsp; value = `True` <br> elif device_indicator_mode == `Inactive` <br> &nbsp; value = `False` |
| cv2.CAP_PROP_AUTO_WB       | bool  | if value == `True` <br> &nbsp; `BalanceWhiteAuto` = `Continuous` <br> else <br> &nbsp; `BalanceWhiteAuto` = `Off` | if balance_white_auto == `Continuous` <br> &nbsp; value = `True` <br> elif balance_white_auto == `Off` <br> &nbsp; value = `False` |

## Command-Line Tool
EasyPySpin provides a command-line tool. Connect the camera and execute the following commands, as shown below, then you can view the captured images.
```sh
EasyPySpin [-h] [-i INDEX] [-e EXPOSURE] [-g GAIN] [-G GAMMA]
           [-b BRIGHTNESS] [-f FPS] [-s SCALE]
```

## External Links
Here are some external links that are useful for using Spinnaker SDK.
* [Spinnaker® SDK Programmer's Guide and API Reference (C++)](http://softwareservices.ptgrey.com/Spinnaker/latest/index.html)
* [Getting Started with Spinnaker SDK on MacOS Applicable products](https://www.flir.com/support-center/iis/machine-vision/application-note/getting-started-with-spinnaker-sdk-on-macos/)
* [Spinnaker Nodes](https://www.flir.com/support-center/iis/machine-vision/application-note/spinnaker-nodes/)
* [Configuring Synchronized Capture with Multiple Cameras](https://www.flir.com/support-center/iis/machine-vision/application-note/configuring-synchronized-capture-with-multiple-cameras)
