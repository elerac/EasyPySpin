# EasyPySpin

EasyPySpin is an unofficial wrapper for FLIR [Spinnaker SDK](https://www.flir.com/products/spinnaker-sdk/). This wrapper provides much the same way as the OpenCV VideoCapture class.


## Usage
### Live streaming
Live streaming will start when `EasyPySpin.py` is executed.
```
python3 EasyPySpin.py
```

### Use as a module
`EasyPySpin.py` can be used as a module.
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
