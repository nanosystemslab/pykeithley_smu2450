"""Keithley 2450 SourceMeter instrument driver over TCP/IP."""

import socket
from enum import Enum
from typing import List
from typing import Optional
from typing import Tuple


class SourceFunction(Enum):
    """SMU source functions."""

    VOLTAGE = "smu.FUNC_DC_VOLTAGE"
    CURRENT = "smu.FUNC_DC_CURRENT"


class MeasureFunction(Enum):
    """SMU measurement functions."""

    DC_VOLTAGE = "smu.FUNC_DC_VOLTAGE"
    DC_CURRENT = "smu.FUNC_DC_CURRENT"
    RESISTANCE = "smu.FUNC_RESISTANCE"


class Sense(Enum):
    """SMU sense modes (2-wire local or 4-wire remote)."""

    TWO_WIRE = "smu.SENSE_2WIRE"
    FOUR_WIRE = "smu.SENSE_4WIRE"


class FilterType(Enum):
    """SMU measurement filter types."""

    REPEAT_AVG = "smu.FILTER_REPEAT_AVG"
    MOVING_AVG = "smu.FILTER_MOVING_AVG"


class SMU2450:
    """Driver for Keithley 2450 SourceMeter.

    Args:
        ip_address: IP address of the instrument.
        port: TCP port number (default 5025).
        timeout: Socket timeout in seconds.
    """

    DEFAULT_PORT = 5025
    DEFAULT_TIMEOUT = 5.0

    def __init__(
        self,
        ip_address: str,
        port: int = DEFAULT_PORT,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize SMU2450 connection parameters."""
        self.ip_address = ip_address
        self.port = port
        self.timeout = timeout
        self._socket: Optional[socket.socket] = None

    def connect(self) -> None:
        """Open TCP connection to the instrument."""
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(self.timeout)
        self._socket.connect((self.ip_address, self.port))

    def disconnect(self) -> None:
        """Close the TCP connection."""
        if self._socket is not None:
            self._socket.close()
            self._socket = None

    def __enter__(self) -> "SMU2450":
        """Connect and return self for use as context manager."""
        self.connect()
        return self

    def __exit__(self, *args: object) -> None:
        """Disconnect on context manager exit."""
        self.disconnect()

    def _check_connection(self) -> socket.socket:
        """Return the socket, raising if not connected."""
        if self._socket is None:
            raise ConnectionError("Not connected. Call connect() first.")
        return self._socket

    def send(self, command: str) -> None:
        """Send a TSP command to the instrument.

        Args:
            command: TSP command string.
        """
        sock = self._check_connection()
        if not command.endswith("\n"):
            command += "\n"
        sock.sendall(command.encode())

    def receive(self, buffer_size: int = 4096) -> str:
        """Read response from the instrument.

        Args:
            buffer_size: Maximum bytes to read.

        Returns:
            Response string with whitespace stripped.
        """
        sock = self._check_connection()
        return sock.recv(buffer_size).decode().strip()

    def query(self, command: str, buffer_size: int = 4096) -> str:
        """Send a command and return the response.

        Args:
            command: TSP command that produces output (use print()).
            buffer_size: Maximum bytes to read.

        Returns:
            Response string.
        """
        self.send(command)
        return self.receive(buffer_size)

    # ── Instrument control ──────────────────────────────────────────

    def reset(self) -> None:
        """Reset the instrument to factory defaults."""
        self.send("reset()")

    def identify(self) -> str:
        """Query the instrument identity string.

        Sends the ``*IDN?`` SCPI command.

        Returns:
            Instrument identification string.
        """
        return self.query("*IDN?")

    # ── Source configuration ────────────────────────────────────────

    def set_source_function(self, func: SourceFunction) -> None:
        """Set the source function.

        Args:
            func: Source function to select (voltage or current).
        """
        self.send(f"smu.source.func = {func.value}")

    def set_source_level(self, level: float) -> None:
        """Set the source output level.

        Args:
            level: Output level in volts or amps for the active
                source function.
        """
        self.send(f"smu.source.level = {level}")

    def set_source_range(self, value: float) -> None:
        """Set the source range.

        Args:
            value: Range value in the unit of the active source function.
        """
        self.send(f"smu.source.range = {value}")

    def set_source_auto_range(self, enable: bool = True) -> None:
        """Enable or disable source auto-range.

        Args:
            enable: True to enable, False to disable.
        """
        state = "smu.ON" if enable else "smu.OFF"
        self.send(f"smu.source.autorange = {state}")

    def set_current_limit(self, limit: float) -> None:
        """Set the current compliance limit when sourcing voltage.

        Args:
            limit: Current limit in amps.
        """
        self.send(f"smu.source.ilimit.level = {limit}")

    def set_voltage_limit(self, limit: float) -> None:
        """Set the voltage compliance limit when sourcing current.

        Args:
            limit: Voltage limit in volts.
        """
        self.send(f"smu.source.vlimit.level = {limit}")

    def set_source_readback(self, enable: bool = True) -> None:
        """Enable or disable source readback.

        When enabled, the instrument measures the actual source value
        instead of reporting the programmed value.

        Args:
            enable: True to enable, False to disable.
        """
        state = "smu.ON" if enable else "smu.OFF"
        self.send(f"smu.source.readback = {state}")

    def set_source_delay(self, delay: float) -> None:
        """Set the source delay.

        Args:
            delay: Delay in seconds between source change and measurement.
        """
        self.send(f"smu.source.delay = {delay}")

    # ── Output control ──────────────────────────────────────────────

    def output_on(self) -> None:
        """Turn the source output on."""
        self.send("smu.source.output = smu.ON")

    def output_off(self) -> None:
        """Turn the source output off."""
        self.send("smu.source.output = smu.OFF")

    # ── Measurement configuration ───────────────────────────────────

    def set_measure_function(self, func: MeasureFunction) -> None:
        """Set the measurement function.

        Args:
            func: Measurement function to select.
        """
        self.send(f"smu.measure.func = {func.value}")

    def set_measure_range(self, value: float) -> None:
        """Set the measurement range.

        Args:
            value: Range value in the unit of the active function.
        """
        self.send(f"smu.measure.range = {value}")

    def set_measure_auto_range(self, enable: bool = True) -> None:
        """Enable or disable measurement auto-range.

        Args:
            enable: True to enable, False to disable.
        """
        state = "smu.ON" if enable else "smu.OFF"
        self.send(f"smu.measure.autorange = {state}")

    def set_nplc(self, nplc: float) -> None:
        """Set the number of power line cycles for integration.

        Args:
            nplc: NPLC value (0.01 to 10).
        """
        self.send(f"smu.measure.nplc = {nplc}")

    def set_sense(self, sense: Sense) -> None:
        """Set 2-wire or 4-wire sense mode.

        Args:
            sense: Sense mode.
        """
        self.send(f"smu.measure.sense = {sense.value}")

    def set_autozero(self, enable: bool = True) -> None:
        """Enable or disable autozero.

        Args:
            enable: True to enable, False to disable.
        """
        state = "smu.ON" if enable else "smu.OFF"
        self.send(f"smu.measure.autozero.enable = {state}")

    # ── Filter configuration ────────────────────────────────────────

    def set_filter(
        self,
        enable: bool = True,
        filter_type: FilterType = FilterType.REPEAT_AVG,
        count: int = 10,
    ) -> None:
        """Configure the measurement filter.

        Args:
            enable: True to enable the filter.
            filter_type: Type of averaging filter.
            count: Number of readings to average.
        """
        self.send(f"smu.measure.filter.type = {filter_type.value}")
        self.send(f"smu.measure.filter.count = {count}")
        state = "smu.ON" if enable else "smu.OFF"
        self.send(f"smu.measure.filter.enable = {state}")

    # ── Measurement ─────────────────────────────────────────────────

    def measure(self) -> float:
        """Take a single measurement with the current configuration.

        Returns:
            Measurement value as a float.
        """
        response = self.query("print(smu.measure.read())")
        return float(response)

    # ── Convenience methods ─────────────────────────────────────────

    def configure_source_voltage(
        self,
        level: float = 0.0,
        current_limit: float = 100e-3,
        measure_range: Optional[float] = None,
        nplc: float = 1,
        four_wire: bool = False,
    ) -> None:
        """Configure to source voltage and measure current.

        Args:
            level: Voltage level in volts.
            current_limit: Current compliance limit in amps.
            measure_range: Current measurement range in amps
                (None for auto-range).
            nplc: Number of power line cycles.
            four_wire: Use 4-wire (remote) sensing if True.
        """
        self.set_source_function(SourceFunction.VOLTAGE)
        self.set_source_level(level)
        self.set_current_limit(current_limit)
        self.set_measure_function(MeasureFunction.DC_CURRENT)
        if measure_range is None:
            self.set_measure_auto_range(True)
        else:
            self.set_measure_range(measure_range)
        self.set_nplc(nplc)
        sense = Sense.FOUR_WIRE if four_wire else Sense.TWO_WIRE
        self.set_sense(sense)

    def configure_source_current(
        self,
        level: float = 0.0,
        voltage_limit: float = 2.0,
        measure_range: Optional[float] = None,
        nplc: float = 1,
        four_wire: bool = False,
    ) -> None:
        """Configure to source current and measure voltage.

        Args:
            level: Current level in amps.
            voltage_limit: Voltage compliance limit in volts.
            measure_range: Voltage measurement range in volts
                (None for auto-range).
            nplc: Number of power line cycles.
            four_wire: Use 4-wire (remote) sensing if True.
        """
        self.set_source_function(SourceFunction.CURRENT)
        self.set_source_level(level)
        self.set_voltage_limit(voltage_limit)
        self.set_measure_function(MeasureFunction.DC_VOLTAGE)
        if measure_range is None:
            self.set_measure_auto_range(True)
        else:
            self.set_measure_range(measure_range)
        self.set_nplc(nplc)
        sense = Sense.FOUR_WIRE if four_wire else Sense.TWO_WIRE
        self.set_sense(sense)

    def configure_resistance(
        self,
        four_wire: bool = True,
        nplc: float = 1,
    ) -> None:
        """Configure for direct resistance measurement.

        Uses the instrument's built-in resistance function, which
        sources a test current and computes V/I automatically.

        Args:
            four_wire: Use 4-wire (remote) sensing if True (default).
            nplc: Number of power line cycles.
        """
        self.set_measure_function(MeasureFunction.RESISTANCE)
        self.set_measure_auto_range(True)
        self.set_nplc(nplc)
        sense = Sense.FOUR_WIRE if four_wire else Sense.TWO_WIRE
        self.set_sense(sense)

    # ── Application-specific configurations ────────────────────────

    def configure_van_der_pauw_source(
        self,
        current: float = 100e-6,
        voltage_limit: float = 2.0,
        nplc: float = 10,
        readback: bool = True,
    ) -> None:
        """Configure as the current source for Van der Pauw measurements.

        Sources a precise DC current through two contacts of the sample
        while a voltmeter (e.g. DMM6500) senses the voltage across the
        other two contacts. Source readback is enabled so the actual
        delivered current can be verified with :meth:`measure`.

        Args:
            current: Source current in amps (default 100uA).
            voltage_limit: Voltage compliance limit in volts (default 2V
                to protect delicate thin-film samples).
            nplc: Power line cycles for integration (default 10 for
                best 60Hz noise rejection).
            readback: Enable source readback (default True).
        """
        self.set_source_function(SourceFunction.CURRENT)
        self.set_source_level(current)
        self.set_voltage_limit(voltage_limit)
        self.set_source_readback(readback)
        self.set_measure_function(MeasureFunction.DC_VOLTAGE)
        self.set_measure_auto_range(True)
        self.set_nplc(nplc)
        self.set_autozero(True)

    # ── Sweeps ──────────────────────────────────────────────────────

    def sweep_linear(
        self,
        start: float,
        stop: float,
        points: int,
        delay: float = -1,
        buffer_name: str = "defbuffer1",
    ) -> None:
        """Configure and run a linear source sweep.

        Sweeps the active source function from start to stop, taking a
        measurement at each point. Blocks until the sweep completes.
        Retrieve results with :meth:`get_buffer_data`.

        Args:
            start: Sweep start level (volts or amps).
            stop: Sweep stop level (volts or amps).
            points: Number of sweep points.
            delay: Delay at each point in seconds (-1 for auto-delay).
            buffer_name: Reading buffer to store results in.
        """
        self.send(f"{buffer_name}.clear()")
        self.send(
            f'smu.source.sweeplinear("sweep", {start}, {stop}, ' f"{points}, {delay})"
        )
        self.send("trigger.model.initiate()")
        self.send("waitcomplete()")

    def get_buffer_count(self, buffer_name: str = "defbuffer1") -> int:
        """Query the number of readings stored in a buffer.

        Args:
            buffer_name: Reading buffer to query.

        Returns:
            Number of readings in the buffer.
        """
        response = self.query(f"print({buffer_name}.n)")
        return int(float(response))

    def get_buffer_data(
        self,
        buffer_name: str = "defbuffer1",
        buffer_size: int = 65536,
    ) -> List[Tuple[float, float]]:
        """Read source values and measurements from a buffer.

        Args:
            buffer_name: Reading buffer to read.
            buffer_size: Maximum bytes to read per query.

        Returns:
            List of (source_value, reading) tuples.
        """
        count = self.get_buffer_count(buffer_name)
        if count == 0:
            return []
        sources = self.query(
            f"printbuffer(1, {count}, {buffer_name}.sourcevalues)",
            buffer_size,
        )
        readings = self.query(
            f"printbuffer(1, {count}, {buffer_name}.readings)",
            buffer_size,
        )
        source_values = [float(v) for v in sources.split(",")]
        reading_values = [float(v) for v in readings.split(",")]
        return list(zip(source_values, reading_values, strict=True))

    def iv_sweep(
        self,
        start: float,
        stop: float,
        points: int = 101,
        current_limit: float = 100e-3,
        delay: float = -1,
    ) -> List[Tuple[float, float]]:
        """Run a voltage sweep and return the I-V curve.

        Configures a voltage source sweep with current measurement,
        runs it, and returns the results. Output is turned off when
        the sweep finishes.

        Args:
            start: Sweep start voltage in volts.
            stop: Sweep stop voltage in volts.
            points: Number of sweep points (default 101).
            current_limit: Current compliance limit in amps.
            delay: Delay at each point in seconds (-1 for auto-delay).

        Returns:
            List of (voltage, current) tuples.
        """
        self.configure_source_voltage(level=start, current_limit=current_limit)
        self.sweep_linear(start, stop, points, delay)
        data = self.get_buffer_data()
        self.output_off()
        return data

    # ── Trigger model ───────────────────────────────────────────────

    def trigger_initiate(self) -> None:
        """Start the trigger model."""
        self.send("trigger.model.initiate()")

    def trigger_abort(self) -> None:
        """Abort the trigger model."""
        self.send("trigger.model.abort()")

    def wait_complete(self, timeout_ms: int = 0) -> None:
        """Wait for all commands to complete.

        Args:
            timeout_ms: Timeout in milliseconds (0 = no timeout).
        """
        if timeout_ms > 0:
            self.send(f"waitcomplete({timeout_ms})")
        else:
            self.send("waitcomplete()")

    # ── Script management ───────────────────────────────────────────

    def load_script(self, name: str, script_path: str) -> None:
        """Upload and run a Lua script on the instrument.

        Args:
            name: Name for the script on the instrument.
            script_path: Local file path to the Lua script.
        """
        with open(script_path) as f:
            contents = f.read()
        self.send(f"if {name} ~= nil then script.delete({name!r}) end")
        self.send(f"loadscript {name}\n{contents}\nendscript")
        self.send(f"{name}()")

    def delete_script(self, name: str) -> None:
        """Delete a script from the instrument.

        Args:
            name: Name of the script to delete.
        """
        self.send(f"script.delete({name!r})")
