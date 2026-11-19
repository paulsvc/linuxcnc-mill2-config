# Mikron WF3 DCM — LinuxCNC EtherCAT Retrofit (`mill2`)

LinuxCNC 2.9 configuration for a **Mikron WF3 DCM** Swiss universal toolroom milling machine retrofitted with **Beckhoff EtherCAT I/O**, **Delta ASDA-A3** AC servo drives (analog $\pm 10\text{ V}$ velocity mode), closed-loop linear scale / encoder feedback, and **Modbus RTU** drive telemetry.

---

## 1. Machine Specifications — Mikron WF3 DCM

The **Mikron WF3 DCM** is a heavy-duty Swiss-built universal tool and cutter CNC milling machine (originally equipped with Heidenhain TNC 135/145/150/155/355 controls).

| Specification | Factory Rating (Mikron WF3 DCM) | Configured in `mill2.ini` |
| :--- | :--- | :--- |
| **X-Axis Travel (Longitudinal)** | `500 mm` | `0.0` to `500.0 mm` (parks at `250.0 mm` after homing) |
| **Y-Axis Travel (Transversal)** | `500 mm` | `0.0` to `500.0 mm` (parks at `250.0 mm` after homing) |
| **Z-Axis Travel (Vertical)** | `385 mm` (`380–400 mm` depending on variant) | `0.0` to `350.0 mm` (parks at `175.0 mm` after homing) |
| **Vertical Quill Stroke** | `90 mm` | Manual quill |
| **Table Clamping Surface** | `800 mm × 450 mm` (rigid / universal angle table) | — |
| **Max Table Load** | `~150–250 kg` (depending on table option) | — |
| **Spindle Taper** | `ISO 40` (`SK 40`), M16 drawbar, hydraulic tool unclamping | Hydraulic unclamping via `EL1018_1.din-0` → `EL2828.dout-0` |
| **Spindle Speed Range** | `31.5 – 3,150 RPM` (up to `4,000 RPM` on overhauled variants) | Closed-loop encoder feedback (`EL5101_ENC`), `0–3,000 RPM` scale |
| **Spindle Motor Power** | `~3.3 – 4.0 kW` (`~8.7 kW / 12 kVA` total machine rating) | Analog speed command (`EL4034.aout-3`), CW/CCW digital outputs |
| **Feed Rate / Rapid Traverse** | `1 – 2,000 mm/min` feed / `3,000 mm/min` rapid | `3,000 mm/min` (`50 mm/s`) on X & Z; `2,100 mm/min` (`35 mm/s`) on Y |
| **Machine Weight** | `~1,800 – 1,950 kg` | — |
| **Footprint (L × W × H)** | `~2.2 m × 1.8 m × 2.0 m` | — |

---

## 2. Control & Retrofit Architecture

- **CNC Controller**: LinuxCNC `2.9` (uspace RT, `1 kHz` / `1,000,000 ns` servo thread) with **AXIS** GUI.
- **Fieldbus**: EtherCAT (`lcec` / `lcec_conf`) running a 13-slave Beckhoff terminal stack at `1 ms` cycle time.
- **Servo Drives**: **Delta ASDA-A3** AC servo drives operating in **analog $\pm 10\text{ V}$ Velocity Mode** (`P1.001 = 0x0002` / `0x0001`), driven by a Beckhoff `EL4034` 4-channel analog output module.
- **Position Feedback**: Closed-loop position feedback in LinuxCNC (`pid.x`, `pid.y`, `pid.z`) using Beckhoff `EL5101` incremental encoder interfaces with index-pulse homing (`HOME_USE_INDEX = YES`).
- **Drive Telemetry (Modbus RTU)**: `mb2hal` polling all 3 Delta ASDA-A3 drives over `/dev/ttyUSB0` (`38400 8N2`) for real-time motor load (%) and hexadecimal alarm codes, displayed in a PyVCP side panel (`monitor.xml`) via `hex_display.py`.
- **Manual Pulse Generator (MPG)**: Physical handwheel wired to `EL1018_2` (`din-4` / `din-6`) with axis selector (`X/Y/Z`) and step multiplier (`0.001 mm`, `0.01 mm`, `0.02 mm`) wired to `EL1008`.
- **Z-Axis Auto-Tune UI**: Embedded **Servo Monitor** tab (`autotune.xml`) in AXIS providing live PID auto-tuning controls and gain readouts.

---

## 3. EtherCAT Hardware Topology (`ethercat-conf.xml`)

Master `0` — `appTimePeriod = 1,000,000 ns` (`1 kHz`), `refClockSyncCycles = 5`:

| Slave Idx | Module | Name | Function / Wiring |
| :---: | :--- | :--- | :--- |
| `0` | **Beckhoff EK1100** | `EK1100` | EtherCAT Coupler |
| `1` | **Beckhoff EL2904** | `EL2904` | 4-Ch TwinSAFE Safety Digital Output |
| `2` | **Beckhoff EL2008** | `EL2008_1` | 8-Ch 24V Digital Output: X enable (`dout-2`), Flood coolant (`dout-3`), Y enable (`dout-4`), Spindle CW (`dout-5`), Z enable (`dout-6`), Spindle CCW (`dout-7`) |
| `3` | **Beckhoff EL1018** | `EL1018_1` | 8-Ch 24V Digital Input: Hydraulic tool unclamping button (`din-0`), X home (`din-1`), Y neg limit (`din-2`), X pos limit (`din-3`), Y pos limit (`din-4`), X neg limit (`din-5`), Y home (`din-6`), Z home (`din-7`) |
| `4` | **Beckhoff EL5101** | `EL5101_X` | Incremental Encoder Interface — **X Axis** (`INPUT_SCALE = -1000`, C-channel index homing) |
| `5` | **Beckhoff EL5101** | `EL5101_Z` | Incremental Encoder Interface — **Z Axis** (`INPUT_SCALE = 1000`, C-channel index homing) |
| `6` | **Beckhoff EL5101** | `EL5101_Y` | Incremental Encoder Interface — **Y Axis** (`INPUT_SCALE = -1100`, C-channel index homing) |
| `7` | **Beckhoff EL4034** | `EL4034` | 4-Ch $\pm 10\text{ V}$ Analog Output: X vel cmd (`aout-0`, scale `200`), Z vel cmd (`aout-1`, scale `-3.8`), Y vel cmd (`aout-2`, scale `140`), Spindle speed (`aout-3`, scale `3000`) |
| `8` | **Beckhoff EL2008** | `EL2008_2` | 8-Ch 24V Digital Output (auxiliary / spare) |
| `9` | **Beckhoff EL1008** | `EL1008` | 8-Ch 24V Digital Input — **MPG Selector**: `x1` (`din-0`), `x10` (`din-1`), `x100` (`din-2`), Axis X (`din-3`), Axis Y (`din-4`), Axis Z (`din-5`), Axis 4 (`din-6`) |
| `10` | **Beckhoff EL1018** | `EL1018_2` | 8-Ch 24V Digital Input: Z neg limit (`din-0`), Z pos limit (`din-2`), MPG Phase A (`din-4`), MPG Phase B (`din-6`) |
| `11` | **Beckhoff EL5101** | `EL5101_ENC` | Incremental Encoder Interface — **Spindle Encoder** (`INPUT_SCALE = -8000`, used for threading/tapping & filtered RPM feedback) |
| `12` | **Beckhoff EL2828** | `EL2828` | 8-Ch 24V Digital Output: Hydraulic tool unclamping valve (`dout-0`), E-Stop enable output (`dout-1`) |

---

## 4. Axis Tuning & Homing Summary (`mill2.ini`)

| Parameter | X Axis (`JOINT_0`) | Y Axis (`JOINT_1`) | Z Axis (`JOINT_2`) | Spindle (`SPINDLE_0`) |
| :--- | :---: | :---: | :---: | :---: |
| **Travel Limits** | `-0.1` to `500.1 mm` | `-0.1` to `500.1 mm` | `-0.1` to `350.1 mm` | — |
| **Homing Sequence** | `2` | `3` | `1` (homes Z first) | — |
| **Home Switch (`HOME_OFFSET`)** | `500.0 mm` | `500.0 mm` | `350.0 mm` | — |
| **Parked Position (`HOME`)** | `250.0 mm` | `250.0 mm` | `175.0 mm` | — |
| **Max Velocity / Accel** | `50 mm/s` / `175 mm/s²` | `35 mm/s` / `175 mm/s²` | `50 mm/s` / `175 mm/s²` | `3000 RPM` scale |
| **PID (`P` / `I` / `D`)** | `65.0` / `0` / `0` | `75.0` / `0` / `0` | `12.0` / `0` / `0` | `0` / `0` / `0` |
| **Feedforward (`FF0` / `FF1` / `FF2`)** | `0` / `1.0` / `0.002` | `0` / `1.0` / `0.002` | `0` / `0.207` / `0.0004` | `1.465` / `0` / `0` |
| **Bias / Deadband** | `0.21` / `0.001` | `0.1` / `0.001` | `0` / `0.001` | `0` / `2` |
| **Input / Output Scale** | `-1000` / `200` | `-1100` / `140` | `1000` / `-3.8` | `-8000` / `3000` |

---

## 5. Repository Structure

| File | Description |
| :--- | :--- |
| `mill2.ini` | Main LinuxCNC configuration (kinematics, axis limits, homing, PID/FF gains, display & PyVCP tabs) |
| `mill2.hal` | Core HAL wiring connecting motion, PID loops, EtherCAT (`lcec`), home/limit switches, spindle, and E-Stop |
| `custom.hal` | Custom HAL logic: hydraulic tool unclamping passthrough, `mb2hal` Modbus RTU, `hex_display.py`, spindle velocity low-pass filter, and MPG handwheel logic |
| `custom_postgui.hal` | Post-GUI HAL connections for the Servo Load/Alarm PyVCP bars (`monitor.xml`) and Z-Axis Auto-Tune tab (`autotune.xml`) |
| `ethercat-conf.xml` | Beckhoff EtherCAT slave chain configuration (`lcec_conf`) |
| `modbus.cfg` | `mb2hal` serial RTU configuration for Delta ASDA-A3 drives (Slave IDs 1, 2, 3 — average load & alarm registers) |
| `monitor.xml` | Right-hand PyVCP panel showing real-time load bars and hex alarm codes for X, Y, and Z drives |
| `autotune.xml` | Embedded **Servo Monitor** PyVCP tab for Z-axis (`pid.z`) auto-tuning and live gain readouts |
| `hex_display.py` | Userspace Python HAL component converting raw Modbus alarm integers to hex display floats and bridging Z auto-tune pins |
| `shutdown.hal` / `tool.tbl` | Shutdown hooks and LinuxCNC tool table |
