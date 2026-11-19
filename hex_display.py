#!/usr/bin/env python3
import hal, time, sys

# Initialize the component
c = hal.component("hex-display")

# Create pins for Drives 1, 2, and 3
for i in range(1, 4):
    c.newpin(f"d{i}-in", hal.HAL_S32, hal.HAL_IN)
    c.newpin(f"d{i}-out", hal.HAL_FLOAT, hal.HAL_OUT)

# Create pins for Z-Axis Auto-Tune UI bridge
c.newpin("z-tune-effort-in", hal.HAL_FLOAT, hal.HAL_IN)
c.newpin("z-tune-cycles-in", hal.HAL_FLOAT, hal.HAL_IN)
c.newpin("z-tune-start-in", hal.HAL_BIT, hal.HAL_IN)
c.newpin("z-tune-running", hal.HAL_BIT, hal.HAL_OUT)
c.newpin("z-pgain-out", hal.HAL_FLOAT, hal.HAL_OUT)
c.newpin("z-igain-out", hal.HAL_FLOAT, hal.HAL_OUT)
c.newpin("z-dgain-out", hal.HAL_FLOAT, hal.HAL_OUT)

c.ready()

last_effort = None
last_cycles = None
last_start = False

try:
    # Ensure tune-type is 0 (PID mode, preserving FF1)
    try:
        hal.set_p("pid.z.tune-type", "0")
    except Exception:
        pass

    while True:
        # 1. Hex alarm display for Drives 1, 2, 3
        for i in range(1, 4):
            val = c[f"d{i}-in"]
            try:
                hex_repr = f"{val:x}"
                c[f"d{i}-out"] = float(hex_repr)
            except (ValueError, TypeError):
                c[f"d{i}-out"] = 0.0

        # 2. Z-Axis Auto-Tune bridge
        try:
            effort = round(float(c["z-tune-effort-in"]), 4)
            if effort > 0 and effort != last_effort:
                hal.set_p("pid.z.tune-effort", str(effort))
                last_effort = effort

            cycles = int(round(float(c["z-tune-cycles-in"])))
            if cycles > 0 and cycles != last_cycles:
                hal.set_p("pid.z.tune-cycles", str(cycles))
                last_cycles = cycles

            start_btn = bool(c["z-tune-start-in"])
            if start_btn and not last_start:
                hal.set_p("pid.z.tune-type", "0")
                hal.set_p("pid.z.tune-start", "1")
            last_start = start_btn

            c["z-tune-running"] = bool(hal.get_value("pid.z.tune-start"))
            c["z-pgain-out"] = float(hal.get_value("pid.z.Pgain"))
            c["z-igain-out"] = float(hal.get_value("pid.z.Igain"))
            c["z-dgain-out"] = float(hal.get_value("pid.z.Dgain"))
        except Exception:
            pass

        time.sleep(0.1)
except KeyboardInterrupt:
    pass
finally:
    hal.exit()
