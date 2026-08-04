# PyKeithley_SMU2450

[![PyPI](https://img.shields.io/pypi/v/pykeithley_smu2450.svg)][pypi status]
[![Status](https://img.shields.io/pypi/status/pykeithley_smu2450.svg)][pypi status]
[![Python Version](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fnanosystemslab%2Fpykeithley_smu2450%2Fmain%2Fpyproject.toml)][pypi status]
[![License](https://img.shields.io/github/license/nanosystemslab/pykeithley_smu2450)][license]

[![Read the Docs](https://img.shields.io/readthedocs/pykeithley-smu2450/latest.svg?label=Read%20the%20Docs)][read the docs]
[![Tests](https://github.com/nanosystemslab/pykeithley_smu2450/workflows/Tests/badge.svg)][tests]
[![Codecov](https://codecov.io/gh/nanosystemslab/pykeithley_smu2450/branch/main/graph/badge.svg)][codecov]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]

[pypi status]: https://pypi.org/project/pykeithley_smu2450/
[read the docs]: https://pykeithley-smu2450.readthedocs.io/
[tests]: https://github.com/nanosystemslab/pykeithley_smu2450/actions?workflow=Tests
[codecov]: https://app.codecov.io/gh/nanosystemslab/pykeithley_smu2450
[pre-commit]: https://github.com/pre-commit/pre-commit
[black]: https://github.com/psf/black

A Python library for controlling the Keithley 2450 SourceMeter (SMU) over Ethernet (TCP/IP). Sends TSP (Test Script Processing) commands directly -- no VISA or NI drivers required.

Companion library to [pykeithley_dmm6500] for the Keithley DMM6500 digital multimeter.

## Features

- TCP/IP connection to the 2450 on port 5025 (no VISA dependency)
- Context manager for automatic connection handling
- Source voltage or current with compliance (current/voltage) limits
- Measure voltage, current, or resistance with 2-wire or 4-wire sensing
- Full control over NPLC, range, autozero, source readback, and measurement filters
- Linear I-V sweeps with reading-buffer retrieval
- Trigger model control (initiate, abort, wait)
- Lua script upload to instrument
- Van der Pauw current-source configuration (pairs with the DMM6500 as voltmeter)
- Command-line interface for quick sourcing, measurement, and sweeps

## Requirements

- Python >= 3.10
- Keithley 2450 connected via Ethernet, with command set switched to **TSP**
  (Menu > Communication > Settings > Command Set on the front panel)
- No additional dependencies (uses only Python standard library)

## Installation

You can install _PyKeithley_SMU2450_ via [pip] from [PyPI]:

```console
$ pip install pykeithley_smu2450
```

Or install from source with Poetry:

```console
$ git clone https://github.com/nanosystemslab/pykeithley_smu2450.git
$ cd pykeithley_smu2450
$ poetry install
```

## Usage

### Python API

```python
from pykeithley_smu2450 import SMU2450

with SMU2450("169.254.11.32") as smu:
    print(smu.identify())

    # Source 1V, measure current (with 10mA compliance limit)
    smu.configure_source_voltage(level=1.0, current_limit=10e-3, nplc=10)
    smu.output_on()
    current = smu.measure()
    smu.output_off()
    print(f"Current: {current:.6e} A")

    # Source 100uA, measure voltage (with 2V compliance limit)
    smu.configure_source_current(level=100e-6, voltage_limit=2.0, nplc=10)
    smu.output_on()
    voltage = smu.measure()
    smu.output_off()
    print(f"Voltage: {voltage:.6e} V")

    # 4-wire resistance measurement
    smu.configure_resistance(four_wire=True, nplc=10)
    smu.output_on()
    resistance = smu.measure()
    smu.output_off()
    print(f"Resistance: {resistance:.4f} ohm")
```

### I-V Sweeps

```python
with SMU2450("169.254.11.32") as smu:
    # Sweep -1V to +1V in 201 points, 10mA compliance
    data = smu.iv_sweep(start=-1.0, stop=1.0, points=201, current_limit=10e-3)
    for voltage, current in data:
        print(f"{voltage:+.4f} V  {current:+.6e} A")
```

### Van der Pauw Measurements (with DMM6500)

The 2450 sources a precise current through two contacts of the sample
while the DMM6500 senses voltage across the other two:

```python
from pykeithley_dmm6500 import DMM6500, sheet_resistance_from_configs
from pykeithley_smu2450 import SMU2450

current = 100e-6

with SMU2450("169.254.11.32") as smu, DMM6500("169.254.11.31") as dmm:
    smu.configure_van_der_pauw_source(current=current, voltage_limit=2.0)
    dmm.configure_van_der_pauw()

    smu.output_on()
    actual_current = smu.measure()  # source readback of delivered current

    # Measure all 4 configurations (swap probes between readings)
    v1 = dmm.measure()  # Config 1
    v2 = dmm.measure()  # Config 2 (reverse of 1)
    v3 = dmm.measure()  # Config 3
    v4 = dmm.measure()  # Config 4 (reverse of 3)
    smu.output_off()

result = sheet_resistance_from_configs(v1, v2, v3, v4, current=actual_current)
print(f"R_sheet: {result.sheet_resistance:.2f} ohm/sq")
```

### Command-Line Interface

```console
# Identify instrument
$ pykeithley_smu2450 169.254.11.32 identify

# Source 1V and measure current (0.1A default compliance)
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

### Hardware Verification

A bench smoke-test script is included to verify a physical unit. Connect
a known resistor (default 10 kOhm) across the front-panel FORCE HI /
FORCE LO terminals and run:

```console
$ ./scripts/hardware_test.sh 169.254.11.32
```

It checks identify/reset, source-voltage and source-current readings
against the expected Ohm's-law values (20% tolerance), runs an I-V
sweep, and forces the output off. Every step is logged to
`logs/hardware-test-<timestamp>/`; on success the script prints the
`git add` / `git commit` commands to record the passing test in the
repository. Use `--resistor OHMS` for a different test resistor and
`--yes` to skip the interactive confirmation. See
[scripts/README.md](scripts/README.md) for the full step-by-step bench
procedure (wiring, TSP mode setup, finding the IP, troubleshooting).

### Docker

A Dockerfile is included for development and testing:

```console
$ docker build -t pykeithley-smu2450-dev .
$ docker run --rm pykeithley-smu2450-dev                         # run tests
$ docker run --rm --network host pykeithley-smu2450-dev poetry run python -c "
from pykeithley_smu2450 import SMU2450
with SMU2450('169.254.11.32') as smu:
    print(smu.identify())
"
```

## Contributing

Contributions are very welcome.
To learn more, see the [Contributor Guide].

## License

Distributed under the terms of the [GPL 3.0 license][license],
_PyKeithley_SMU2450_ is free and open source software.

## Issues

If you encounter any problems,
please [file an issue] along with a detailed description.

## Credits

This project was generated from [@nanosystemslab]'s [Nanosystems Lab Python Cookiecutter] template.

[@nanosystemslab]: https://github.com/nanosystemslab
[pypi]: https://pypi.org/
[pykeithley_dmm6500]: https://github.com/nanosystemslab/pykeithley_dmm6500
[nanosystems lab python cookiecutter]: https://github.com/nanosystemslab/cookiecutter-nanosystemslab
[file an issue]: https://github.com/nanosystemslab/pykeithley_smu2450/issues
[pip]: https://pip.pypa.io/

<!-- github-only -->

[license]: https://github.com/nanosystemslab/pykeithley_smu2450/blob/main/LICENSE
[contributor guide]: https://github.com/nanosystemslab/pykeithley_smu2450/blob/main/CONTRIBUTING.md
[command-line reference]: https://pykeithley-smu2450.readthedocs.io/en/latest/usage.html
