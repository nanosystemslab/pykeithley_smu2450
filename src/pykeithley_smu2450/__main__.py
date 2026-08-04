"""Command-line interface."""

import argparse
import time

from pykeithley_smu2450.smu2450 import SMU2450


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="pykeithley_smu2450",
        description="Keithley 2450 SourceMeter command-line tool",
    )
    parser.add_argument(
        "ip_address",
        help="IP address of the SMU2450",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=SMU2450.DEFAULT_PORT,
        help="TCP port (default: %(default)s)",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("identify", help="Query instrument identity (*IDN?)")

    sourcev_parser = sub.add_parser(
        "sourcev", help="Source voltage and measure current"
    )
    sourcev_parser.add_argument(
        "level",
        type=float,
        help="Voltage level in volts",
    )
    sourcev_parser.add_argument(
        "--limit",
        type=float,
        default=100e-3,
        help="Current compliance limit in amps (default: 0.1)",
    )
    sourcev_parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=1,
        help="Number of readings (default: 1)",
    )
    sourcev_parser.add_argument(
        "-d",
        "--delay",
        type=float,
        default=0.5,
        help="Delay between readings in seconds (default: 0.5)",
    )
    sourcev_parser.add_argument(
        "--nplc",
        type=float,
        default=1,
        help="NPLC value (default: 1)",
    )

    sourcei_parser = sub.add_parser(
        "sourcei", help="Source current and measure voltage"
    )
    sourcei_parser.add_argument(
        "level",
        type=float,
        help="Current level in amps",
    )
    sourcei_parser.add_argument(
        "--limit",
        type=float,
        default=2.0,
        help="Voltage compliance limit in volts (default: 2.0)",
    )
    sourcei_parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=1,
        help="Number of readings (default: 1)",
    )
    sourcei_parser.add_argument(
        "-d",
        "--delay",
        type=float,
        default=0.5,
        help="Delay between readings in seconds (default: 0.5)",
    )
    sourcei_parser.add_argument(
        "--nplc",
        type=float,
        default=1,
        help="NPLC value (default: 1)",
    )

    sweep_parser = sub.add_parser(
        "sweep", help="Run an I-V voltage sweep and print CSV data"
    )
    sweep_parser.add_argument(
        "start",
        type=float,
        help="Sweep start voltage in volts",
    )
    sweep_parser.add_argument(
        "stop",
        type=float,
        help="Sweep stop voltage in volts",
    )
    sweep_parser.add_argument(
        "--points",
        type=int,
        default=101,
        help="Number of sweep points (default: 101)",
    )
    sweep_parser.add_argument(
        "--limit",
        type=float,
        default=100e-3,
        help="Current compliance limit in amps (default: 0.1)",
    )

    sub.add_parser("off", help="Turn the source output off")

    sub.add_parser("reset", help="Reset instrument to factory defaults")

    return parser


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    return create_parser().parse_args()


def _read_loop(smu: SMU2450, count: int, delay: float) -> None:
    """Turn output on, print readings, and turn output off.

    Args:
        smu: Connected instrument.
        count: Number of readings to take.
        delay: Delay between readings in seconds.
    """
    smu.output_on()
    try:
        for i in range(count):
            value = smu.measure()
            print(f"{value:+.8e}")
            if i < count - 1:
                time.sleep(delay)
    finally:
        smu.output_off()


def main() -> None:
    """PyKeithley_SMU2450."""
    args = parse_args()

    with SMU2450(args.ip_address, port=args.port) as smu:
        if args.command == "identify":
            print(smu.identify())

        elif args.command == "reset":
            smu.reset()
            print("Instrument reset.")

        elif args.command == "off":
            smu.output_off()
            print("Output off.")

        elif args.command == "sourcev":
            smu.configure_source_voltage(
                level=args.level,
                current_limit=args.limit,
                nplc=args.nplc,
            )
            _read_loop(smu, args.count, args.delay)

        elif args.command == "sourcei":
            smu.configure_source_current(
                level=args.level,
                voltage_limit=args.limit,
                nplc=args.nplc,
            )
            _read_loop(smu, args.count, args.delay)

        elif args.command == "sweep":
            data = smu.iv_sweep(
                start=args.start,
                stop=args.stop,
                points=args.points,
                current_limit=args.limit,
            )
            print("voltage,current")
            for voltage, current in data:
                print(f"{voltage:+.8e},{current:+.8e}")


if __name__ == "__main__":
    main()
