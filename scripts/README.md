# Hardware Test Walkthrough

Step-by-step bench procedure for verifying a physical Keithley 2450
SourceMeter with `hardware_test.sh`. Follow the steps in order; the
whole check takes about 10 minutes.

## What You Need

- Keithley 2450 SourceMeter with a power cord
- Ethernet cable (direct to your computer, or to the lab switch)
- One resistor of known value, nominally **10 kOhm** (1/4 W is plenty:
  worst case here is 1 V across 10 kOhm = 0.1 mW). Any value from
  1 kOhm to 100 kOhm works if you pass `--resistor`.
- Two test leads (banana plugs) or a component test fixture
- This repository cloned locally, with either Poetry installed
  (`poetry install` run once) or plain Python 3.10+

## Step 1 -- Connect the Test Resistor

1. Make sure the **OUTPUT is off** (the front-panel OUTPUT light should
   be dark).
2. Connect the resistor between the front-panel **FORCE HI** (red) and
   **FORCE LO** (black) banana jacks. Leave SENSE HI/LO unconnected --
   this test uses 2-wire sensing.
3. On the front panel, confirm the **TERMINALS** setting is **FRONT**
   (Home screen, bottom edge; or the FRONT/REAR indicator).

## Step 2 -- Set the Instrument to TSP Mode

The library speaks TSP, but the 2450 ships in SCPI mode. One-time
setup:

1. Press **MENU**.
2. Under **System**, select **Settings**.
3. Set **Command Set** to **TSP**.
4. The instrument will prompt to reboot -- accept and wait for it to
   restart.

If this is skipped, Step 5 fails on the very first `identify` check
(the instrument ignores TSP commands or returns errors).

## Step 3 -- Connect Ethernet and Find the IP Address

1. Plug in the Ethernet cable.
2. Press **MENU** > **Communication** > **LAN**.
3. Note the **IP Address** shown (e.g. `169.254.11.32`).
   - Direct cable to a computer: the 2450 auto-assigns a link-local
     `169.254.x.x` address after ~30 seconds. Your computer will do the
     same and they can talk directly.
   - Lab network: it gets a DHCP address from the switch.
4. Sanity-check connectivity from your computer:

   ```console
   $ ping <ip-address>
   ```

   If ping fails, fix networking before continuing (see
   Troubleshooting below).

## Step 4 -- Run the Test Script

From the repository root:

```console
$ cd pykeithley_smu2450
$ ./scripts/hardware_test.sh <ip-address>
```

If your resistor is not 10 kOhm, say so:

```console
$ ./scripts/hardware_test.sh <ip-address> --resistor 4700
```

The script shows a checklist of Steps 1-3 and waits for **Enter**
before touching the instrument. Press Enter to start.

## Step 5 -- Watch the Six Checks

Each step prints the command it runs, the instrument's response, and
PASS or FAIL:

| #   | Step           | What it proves                                       |
| --- | -------------- | ---------------------------------------------------- |
| 1   | identify       | TCP connectivity and TSP mode (IDN mentions 2450)    |
| 2   | reset          | Instrument accepts commands, known starting state    |
| 3   | source-voltage | Sources 1 V, measured current ~ V/R (within 20%)     |
| 4   | source-current | Sources 100 uA, measured voltage ~ I\*R (within 20%) |
| 5   | iv-sweep       | 11-point 0-1 V sweep returns a full CSV I-V curve    |
| 6   | output-off     | Source output is safely off at the end               |

Steps 3 and 4 are the real physics check: the measured values must
match Ohm's law for your resistor to within 20% (loose enough for a
5%-tolerance resistor plus lead resistance, tight enough to catch a
wrong range, wrong wiring, or a broken channel).

While Step 3/4 runs you should see the front-panel OUTPUT light come
on briefly, then go off.

## Step 6 -- Commit the Logs

Every run writes a timestamped directory:

```
logs/hardware-test-<timestamp>/
    00-meta.log            date, host, IP, resistor, git commit, python
    01-identify.log        raw output of each step...
    02-reset.log
    03-source-voltage.log
    04-source-current.log
    05-iv-sweep.log        the I-V curve as CSV
    06-output-off.log
    summary.log            one-line PASS/FAIL per check
```

**If everything passed**, the script prints the exact commands to
record the verified instrument in the repository -- run them:

```console
$ git add logs/hardware-test-<timestamp>
$ git commit -m "Add passing 2450 hardware test logs (<timestamp>)"
```

**If anything failed**, do not commit. Read `summary.log` and the
failing step's log, fix the cause (see below), and re-run. Each re-run
gets a fresh log directory; only commit the passing one.

## Troubleshooting

| Symptom                                                | Likely cause                                          | Fix                                                                       |
| ------------------------------------------------------ | ----------------------------------------------------- | ------------------------------------------------------------------------- |
| `identify` times out                                   | Wrong IP, cable unplugged, or firewall                | Re-check Step 3, `ping` the instrument                                    |
| `identify` hangs or returns garbage                    | Instrument in SCPI mode                               | Do Step 2 (Command Set = TSP)                                             |
| Current/voltage check FAIL, reading ~0                 | Resistor not connected, or TERMINALS set to REAR      | Re-check Step 1                                                           |
| Current/voltage check FAIL, off by a fixed factor      | Wrong resistor value assumed                          | Re-run with `--resistor <actual-ohms>`                                    |
| Voltage reading pinned at the limit                    | Compliance reached (resistor much larger than stated) | Check resistor value; the script sets the voltage limit from it           |
| Script says `command not found: poetry` fallbacks fail | No Python environment                                 | `poetry install` in the repo root, or ensure `python3` >= 3.10 is on PATH |

## Safety Notes

- The test never exceeds 1 V / 10 mA (0.1 mW into a 10 kOhm resistor)
  -- safe for any common resistor.
- The script always ends by forcing the output off (Step 6), even
  after a failed source step. If you abort mid-run with Ctrl-C, press
  the front-panel **OUTPUT** button or turn it off from the CLI:

  ```console
  $ pykeithley_smu2450 <ip-address> off
  ```

  Either way, check that the OUTPUT light is dark before walking away.
