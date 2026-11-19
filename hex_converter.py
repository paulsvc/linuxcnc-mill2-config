#!/usr/bin/env python3
import hal, time

h = hal.component("hex-conv")
h.newpin("in", hal.HAL_S32, hal.HAL_IN)
h.newpin("out-string", hal.HAL_PORT, hal.HAL_OUT) # Needs a string-capable pin
h.ready()

try:
    while True:
        # Convert integer 34 to hex string "22"
        h['out-string'] = f"{h['in']:02x}".upper()
        time.sleep(0.1)
except KeyboardInterrupt:
    raise SystemExit
