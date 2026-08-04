# Usage

## Installation

Install from PyPI:

```console
$ pip install pykeithley_smu2450
```

Or install from source with Poetry:

```console
$ git clone https://github.com/nanosystemslab/pykeithley_smu2450.git
$ cd pykeithley_smu2450
$ poetry install
```

## Python API

### Connecting

The instrument must be set to the **TSP** command set
(Menu > Communication > Settings > Command Set on the front panel).

Use the context manager for automatic connection handling:

```python
from pykeithley_smu2450 import SMU2450

with SMU2450("169.254.11.32") as smu:
    print(smu.identify())
```

Or manage the connection manually:

```python
smu = SMU2450("169.254.11.32")
smu.connect()
print(smu.identify())
smu.disconnect()
```

### Source Voltage, Measure Current

```python
with SMU2450("169.254.11.32") as smu:
    smu.configure_source_voltage(level=1.0, current_limit=10e-3, nplc=10)
    smu.output_on()
    current = smu.measure()
    smu.output_off()
    print(f"Current: {current:.6e} A")
```

### Source Current, Measure Voltage

```python
with SMU2450("169.254.11.32") as smu:
    smu.configure_source_current(level=100e-6, voltage_limit=2.0, nplc=10)
    smu.output_on()
    voltage = smu.measure()
    smu.output_off()
    print(f"Voltage: {voltage:.6e} V")
```

### Resistance Measurement

```python
with SMU2450("169.254.11.32") as smu:
    # 4-wire (remote sense) resistance, best for low resistances
    smu.configure_resistance(four_wire=True, nplc=10)
    smu.output_on()
    resistance = smu.measure()
    smu.output_off()
    print(f"Resistance: {resistance:.4f} ohm")
```

### I-V Sweeps

```python
with SMU2450("169.254.11.32") as smu:
    data = smu.iv_sweep(start=-1.0, stop=1.0, points=201, current_limit=10e-3)
    for voltage, current in data:
        print(f"{voltage:+.4f} V  {current:+.6e} A")
```

For full control, configure the source first and use
`sweep_linear` / `get_buffer_data` directly:

```python
with SMU2450("169.254.11.32") as smu:
    smu.configure_source_current(level=0, voltage_limit=10)
    smu.sweep_linear(start=0, stop=1e-3, points=101, delay=0.1)
    data = smu.get_buffer_data()
    smu.output_off()
```

### Measurement Filter

```python
from pykeithley_smu2450 import FilterType

with SMU2450("169.254.11.32") as smu:
    smu.configure_source_current(level=100e-6, voltage_limit=2.0)
    smu.set_filter(enable=True, filter_type=FilterType.REPEAT_AVG, count=100)
    smu.output_on()
    voltage = smu.measure()
    smu.output_off()
```

### Van der Pauw Current Source

Pairs with the DMM6500 as the voltage sensor:

```python
with SMU2450("169.254.11.32") as smu:
    smu.configure_van_der_pauw_source(current=100e-6, voltage_limit=2.0)
    smu.output_on()
    actual_current = smu.measure()  # source readback
    # ... sense voltages with the DMM ...
    smu.output_off()
```

### Raw TSP Commands

Any TSP command can be sent directly:

```python
with SMU2450("169.254.11.32") as smu:
    smu.send("smu.source.delay = 0.5")
    level = smu.query("print(smu.source.level)")
```

## Command-Line Interface

```console
# Identify instrument
$ pykeithley_smu2450 169.254.11.32 identify

# Source 1V and measure current with 10mA compliance
$ pykeithley_smu2450 169.254.11.32 sourcev 1.0 --limit 0.01

# Source 100uA and take 10 voltage readings, 1s apart
$ pykeithley_smu2450 169.254.11.32 sourcei 100e-6 --limit 2.0 -n 10 -d 1.0

# I-V sweep from -1V to 1V, print CSV (note the -- before negative values)
$ pykeithley_smu2450 169.254.11.32 sweep --points 201 -- -1.0 1.0

# Turn output off
$ pykeithley_smu2450 169.254.11.32 off

# Reset instrument
$ pykeithley_smu2450 169.254.11.32 reset
```
