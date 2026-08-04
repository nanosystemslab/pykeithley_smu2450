"""Test cases for the pykeithley_smu2450 package."""

import pathlib
from typing import Generator
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from pykeithley_smu2450 import SMU2450
from pykeithley_smu2450 import FilterType
from pykeithley_smu2450 import MeasureFunction
from pykeithley_smu2450 import Sense
from pykeithley_smu2450 import SourceFunction


@pytest.fixture
def mock_socket() -> Generator[MagicMock, None, None]:
    """Create a mock socket for testing without hardware."""
    with patch("pykeithley_smu2450.smu2450.socket.socket") as mock_sock_cls:
        mock_sock = MagicMock()
        mock_sock_cls.return_value = mock_sock
        yield mock_sock


@pytest.fixture
def smu(mock_socket: MagicMock) -> SMU2450:
    """Create a connected SMU2450 instance with mocked socket."""
    instrument = SMU2450("192.168.1.1")
    instrument.connect()
    return instrument


class TestConnection:
    """Test connection management."""

    def test_connect(self, mock_socket: MagicMock) -> None:
        """Test TCP connection to instrument."""
        smu = SMU2450("192.168.1.1", port=5025)
        smu.connect()
        mock_socket.settimeout.assert_called_once_with(5.0)
        mock_socket.connect.assert_called_once_with(("192.168.1.1", 5025))

    def test_disconnect(self, smu: SMU2450, mock_socket: MagicMock) -> None:
        """Test disconnection closes socket."""
        smu.disconnect()
        mock_socket.close.assert_called_once()
        assert smu._socket is None

    def test_context_manager(self, mock_socket: MagicMock) -> None:
        """Test context manager connects and disconnects."""
        with SMU2450("192.168.1.1"):
            mock_socket.connect.assert_called_once()
        mock_socket.close.assert_called_once()

    def test_send_without_connection_raises(self) -> None:
        """Test sending without connection raises error."""
        smu = SMU2450("192.168.1.1")
        with pytest.raises(ConnectionError):
            smu.send("reset()")


class TestSendReceive:
    """Test command send/receive."""

    def test_send_appends_newline(self, smu: SMU2450, mock_socket: MagicMock) -> None:
        """Test that send appends newline."""
        smu.send("reset()")
        mock_socket.sendall.assert_called_with(b"reset()\n")

    def test_send_no_double_newline(self, smu: SMU2450, mock_socket: MagicMock) -> None:
        """Test that send does not double newline."""
        smu.send("reset()\n")
        mock_socket.sendall.assert_called_with(b"reset()\n")

    def test_query(self, smu: SMU2450, mock_socket: MagicMock) -> None:
        """Test query sends command and returns response."""
        mock_socket.recv.return_value = b"1.23456e-03\n"
        result = smu.query("print(smu.measure.read())")
        assert result == "1.23456e-03"


class TestSourceConfiguration:
    """Test source configuration."""

    def test_set_source_function(self, smu: SMU2450, mock_socket: MagicMock) -> None:
        """Test setting source function."""
        smu.set_source_function(SourceFunction.CURRENT)
        mock_socket.sendall.assert_called_with(
            b"smu.source.func = smu.FUNC_DC_CURRENT\n"
        )

    def test_set_source_level(self, smu: SMU2450, mock_socket: MagicMock) -> None:
        """Test setting source level."""
        smu.set_source_level(1.5)
        mock_socket.sendall.assert_called_with(b"smu.source.level = 1.5\n")

    def test_set_source_range(self, smu: SMU2450, mock_socket: MagicMock) -> None:
        """Test setting source range."""
        smu.set_source_range(2)
        mock_socket.sendall.assert_called_with(b"smu.source.range = 2\n")

    def test_set_current_limit(self, smu: SMU2450, mock_socket: MagicMock) -> None:
        """Test setting current compliance limit."""
        smu.set_current_limit(0.001)
        mock_socket.sendall.assert_called_with(b"smu.source.ilimit.level = 0.001\n")

    def test_set_voltage_limit(self, smu: SMU2450, mock_socket: MagicMock) -> None:
        """Test setting voltage compliance limit."""
        smu.set_voltage_limit(2.0)
        mock_socket.sendall.assert_called_with(b"smu.source.vlimit.level = 2.0\n")

    def test_set_source_readback(self, smu: SMU2450, mock_socket: MagicMock) -> None:
        """Test enabling source readback."""
        smu.set_source_readback(True)
        mock_socket.sendall.assert_called_with(b"smu.source.readback = smu.ON\n")


class TestOutputControl:
    """Test output on/off control."""

    def test_output_on(self, smu: SMU2450, mock_socket: MagicMock) -> None:
        """Test turning output on."""
        smu.output_on()
        mock_socket.sendall.assert_called_with(b"smu.source.output = smu.ON\n")

    def test_output_off(self, smu: SMU2450, mock_socket: MagicMock) -> None:
        """Test turning output off."""
        smu.output_off()
        mock_socket.sendall.assert_called_with(b"smu.source.output = smu.OFF\n")


class TestMeasureConfiguration:
    """Test measurement configuration."""

    def test_set_measure_function(self, smu: SMU2450, mock_socket: MagicMock) -> None:
        """Test setting measurement function."""
        smu.set_measure_function(MeasureFunction.DC_CURRENT)
        mock_socket.sendall.assert_called_with(
            b"smu.measure.func = smu.FUNC_DC_CURRENT\n"
        )

    def test_set_measure_range(self, smu: SMU2450, mock_socket: MagicMock) -> None:
        """Test setting measurement range."""
        smu.set_measure_range(0.001)
        mock_socket.sendall.assert_called_with(b"smu.measure.range = 0.001\n")

    def test_set_nplc(self, smu: SMU2450, mock_socket: MagicMock) -> None:
        """Test setting NPLC."""
        smu.set_nplc(10)
        mock_socket.sendall.assert_called_with(b"smu.measure.nplc = 10\n")

    def test_set_sense_4wire(self, smu: SMU2450, mock_socket: MagicMock) -> None:
        """Test setting 4-wire sense mode."""
        smu.set_sense(Sense.FOUR_WIRE)
        mock_socket.sendall.assert_called_with(b"smu.measure.sense = smu.SENSE_4WIRE\n")

    def test_set_autozero(self, smu: SMU2450, mock_socket: MagicMock) -> None:
        """Test setting autozero."""
        smu.set_autozero(True)
        mock_socket.sendall.assert_called_with(
            b"smu.measure.autozero.enable = smu.ON\n"
        )

    def test_set_filter(self, smu: SMU2450, mock_socket: MagicMock) -> None:
        """Test setting measurement filter."""
        smu.set_filter(enable=True, filter_type=FilterType.REPEAT_AVG, count=100)
        calls = [c.args[0] for c in mock_socket.sendall.call_args_list]
        assert b"smu.measure.filter.type = smu.FILTER_REPEAT_AVG\n" in calls
        assert b"smu.measure.filter.count = 100\n" in calls
        assert b"smu.measure.filter.enable = smu.ON\n" in calls


class TestMeasurement:
    """Test measurement methods."""

    def test_measure(self, smu: SMU2450, mock_socket: MagicMock) -> None:
        """Test taking a measurement."""
        mock_socket.recv.return_value = b"1.00234e-03\n"
        value = smu.measure()
        assert isinstance(value, float)
        assert value == pytest.approx(1.00234e-03)

    def test_configure_source_voltage(
        self, smu: SMU2450, mock_socket: MagicMock
    ) -> None:
        """Test source voltage configuration."""
        smu.configure_source_voltage(level=1.0, current_limit=0.01, nplc=10)
        calls = [c.args[0] for c in mock_socket.sendall.call_args_list]
        assert b"smu.source.func = smu.FUNC_DC_VOLTAGE\n" in calls
        assert b"smu.source.level = 1.0\n" in calls
        assert b"smu.source.ilimit.level = 0.01\n" in calls
        assert b"smu.measure.func = smu.FUNC_DC_CURRENT\n" in calls
        assert b"smu.measure.autorange = smu.ON\n" in calls
        assert b"smu.measure.nplc = 10\n" in calls
        assert b"smu.measure.sense = smu.SENSE_2WIRE\n" in calls

    def test_configure_source_current(
        self, smu: SMU2450, mock_socket: MagicMock
    ) -> None:
        """Test source current configuration."""
        smu.configure_source_current(level=100e-6, voltage_limit=2.0, four_wire=True)
        calls = [c.args[0] for c in mock_socket.sendall.call_args_list]
        assert b"smu.source.func = smu.FUNC_DC_CURRENT\n" in calls
        assert b"smu.source.level = 0.0001\n" in calls
        assert b"smu.source.vlimit.level = 2.0\n" in calls
        assert b"smu.measure.func = smu.FUNC_DC_VOLTAGE\n" in calls
        assert b"smu.measure.sense = smu.SENSE_4WIRE\n" in calls

    def test_configure_source_manual_range(
        self, smu: SMU2450, mock_socket: MagicMock
    ) -> None:
        """Test source configuration with manual measure range."""
        smu.configure_source_voltage(level=1.0, measure_range=0.001)
        calls = [c.args[0] for c in mock_socket.sendall.call_args_list]
        assert b"smu.measure.range = 0.001\n" in calls
        assert b"smu.measure.autorange = smu.ON\n" not in calls

    def test_configure_resistance(self, smu: SMU2450, mock_socket: MagicMock) -> None:
        """Test resistance configuration defaults to 4-wire."""
        smu.configure_resistance()
        calls = [c.args[0] for c in mock_socket.sendall.call_args_list]
        assert b"smu.measure.func = smu.FUNC_RESISTANCE\n" in calls
        assert b"smu.measure.sense = smu.SENSE_4WIRE\n" in calls


class TestVanDerPauw:
    """Test Van der Pauw source configuration."""

    def test_configure_van_der_pauw_source_defaults(
        self, smu: SMU2450, mock_socket: MagicMock
    ) -> None:
        """Test default VdP source configuration."""
        smu.configure_van_der_pauw_source()
        calls = [c.args[0] for c in mock_socket.sendall.call_args_list]
        assert b"smu.source.func = smu.FUNC_DC_CURRENT\n" in calls
        assert b"smu.source.level = 0.0001\n" in calls
        assert b"smu.source.vlimit.level = 2.0\n" in calls
        assert b"smu.source.readback = smu.ON\n" in calls
        assert b"smu.measure.func = smu.FUNC_DC_VOLTAGE\n" in calls
        assert b"smu.measure.nplc = 10\n" in calls
        assert b"smu.measure.autozero.enable = smu.ON\n" in calls

    def test_configure_van_der_pauw_source_custom_current(
        self, smu: SMU2450, mock_socket: MagicMock
    ) -> None:
        """Test VdP source configuration with custom current."""
        smu.configure_van_der_pauw_source(current=1e-3, voltage_limit=5.0)
        calls = [c.args[0] for c in mock_socket.sendall.call_args_list]
        assert b"smu.source.level = 0.001\n" in calls
        assert b"smu.source.vlimit.level = 5.0\n" in calls


class TestSweep:
    """Test sweep configuration and buffer readout."""

    def test_sweep_linear(self, smu: SMU2450, mock_socket: MagicMock) -> None:
        """Test linear sweep commands."""
        smu.sweep_linear(0, 1, 11, delay=-1)
        calls = [c.args[0] for c in mock_socket.sendall.call_args_list]
        assert b"defbuffer1.clear()\n" in calls
        assert b'smu.source.sweeplinear("sweep", 0, 1, 11, -1)\n' in calls
        assert b"trigger.model.initiate()\n" in calls
        assert b"waitcomplete()\n" in calls

    def test_get_buffer_count(self, smu: SMU2450, mock_socket: MagicMock) -> None:
        """Test querying buffer count."""
        mock_socket.recv.return_value = b"11.0\n"
        assert smu.get_buffer_count() == 11

    def test_get_buffer_data(self, smu: SMU2450, mock_socket: MagicMock) -> None:
        """Test reading buffer data as (source, reading) pairs."""
        mock_socket.recv.side_effect = [
            b"3.0\n",
            b"0.0, 0.5, 1.0\n",
            b"0.0, 1.0e-03, 2.0e-03\n",
        ]
        data = smu.get_buffer_data()
        assert data == [
            (0.0, 0.0),
            (0.5, pytest.approx(1.0e-03)),
            (1.0, pytest.approx(2.0e-03)),
        ]

    def test_get_buffer_data_empty(self, smu: SMU2450, mock_socket: MagicMock) -> None:
        """Test reading an empty buffer returns empty list."""
        mock_socket.recv.return_value = b"0.0\n"
        assert smu.get_buffer_data() == []

    def test_iv_sweep_turns_output_off(
        self, smu: SMU2450, mock_socket: MagicMock
    ) -> None:
        """Test IV sweep reads data and turns output off."""
        mock_socket.recv.side_effect = [
            b"2.0\n",
            b"0.0, 1.0\n",
            b"0.0, 1.0e-03\n",
        ]
        data = smu.iv_sweep(0, 1, points=2)
        assert len(data) == 2
        calls = [c.args[0] for c in mock_socket.sendall.call_args_list]
        assert b"smu.source.output = smu.OFF\n" in calls


class TestTrigger:
    """Test trigger model control."""

    def test_trigger_initiate(self, smu: SMU2450, mock_socket: MagicMock) -> None:
        """Test trigger initiation."""
        smu.trigger_initiate()
        mock_socket.sendall.assert_called_with(b"trigger.model.initiate()\n")

    def test_trigger_abort(self, smu: SMU2450, mock_socket: MagicMock) -> None:
        """Test trigger abort."""
        smu.trigger_abort()
        mock_socket.sendall.assert_called_with(b"trigger.model.abort()\n")

    def test_wait_complete(self, smu: SMU2450, mock_socket: MagicMock) -> None:
        """Test wait for completion."""
        smu.wait_complete()
        mock_socket.sendall.assert_called_with(b"waitcomplete()\n")


class TestReset:
    """Test instrument control."""

    def test_reset(self, smu: SMU2450, mock_socket: MagicMock) -> None:
        """Test instrument reset."""
        smu.reset()
        mock_socket.sendall.assert_called_with(b"reset()\n")

    def test_identify(self, smu: SMU2450, mock_socket: MagicMock) -> None:
        """Test instrument identification."""
        mock_socket.recv.return_value = (
            b"KEITHLEY INSTRUMENTS,MODEL 2450,04110234,1.7.12b\n"
        )
        idn = smu.identify()
        assert "2450" in idn


class TestScriptManagement:
    """Test Lua script upload."""

    def test_load_script(
        self, smu: SMU2450, mock_socket: MagicMock, tmp_path: pathlib.Path
    ) -> None:
        """Test uploading a Lua script."""
        script = tmp_path / "test.lua"
        script.write_text('print("hello")')
        smu.load_script("myscript", str(script))
        calls = [c.args[0] for c in mock_socket.sendall.call_args_list]
        assert any(b"loadscript myscript" in c for c in calls)
        assert any(b"myscript()" in c for c in calls)
