#!/usr/bin/env python3
"""Bench test for Bolt: checks every sensor before assembly.

Plug a sensor into the Robot HAT on the table, switch the battery on, then test it on its own:
    sudo python3 bench_test.py touch

Tests: i2c, battery, speaker, leds, ultrasonic, touch, sound, imu, camera.
Test one loose servo plugged into port P0 to P11 (it wiggles, then parks at 0):
    sudo python3 bench_test.py servo 3
Run with no name to test every sensor in one go:
    sudo python3 bench_test.py

Each test tells you what to do (wave a hand, touch, clap...) and prints PASS or FAIL.
The V1 Robot HAT has no microphone, so there is no mic test.
"""

import subprocess
import sys
import time

results = {}
bolt = None


def run(name, test):
    print(f"\n=== {name} ===")
    try:
        results[name] = bool(test())
    except Exception as e:
        print(f"  error: {e}")
        results[name] = False
    print("  PASS" if results[name] else "  FAIL")


def i2c():
    out = subprocess.run(["i2cdetect", "-y", "1"], capture_output=True, text=True).stdout
    found = {a for line in out.splitlines()[1:] for a in line.split()[1:]}
    for addr, part in [("14", "Robot HAT"), ("36", "IMU"), ("74", "LED strip")]:
        print(f"  0x{addr} {part}: {'found' if addr in found else 'missing'}")
    return "14" in found


def battery():
    from robot_hat import utils
    v = utils.get_battery_voltage()
    print(f"  battery: {v:.2f} V (full is about 8.4 V, charge below 7 V)")
    return v > 6.5


def servo(port):
    from robot_hat import Servo
    from robot_hat.utils import reset_mcu
    reset_mcu()
    time.sleep(1)
    s = Servo(port)
    print(f"  The servo on P{port} should turn one way, then the other, then stop in the middle.")
    for angle in (30, -30, 30, -30, 0):
        s.angle(angle)
        time.sleep(0.6)
    return input("  Did it move smoothly? (y/n) ").strip().lower().startswith("y")


def speaker():
    if not hasattr(bolt, "music"):
        print("  Sound player didn't start. If you used sudo, try again without it.")
        return False
    print("  You should hear 5 long barks.")
    for i in range(5):
        print(f"  bark {i + 1}")
        # Two barks back to back make one longer bark
        bolt.speak_block("single_bark_1", volume=80)
        bolt.speak_block("single_bark_2", volume=80)
        time.sleep(0.5)
    return input("  Did you hear all 5? (y/n) ").strip().lower().startswith("y")


def leds():
    bolt.rgb_strip.set_mode("breath", "cyan", bps=1)
    print("  The LED strip should glow cyan.")
    ok = input("  Is it glowing? (y/n) ").strip().lower().startswith("y")
    bolt.rgb_strip.close()
    return ok


def ultrasonic():
    print("  Move your hand closer to and further from the sensor for 5 seconds.")
    readings = []
    for _ in range(10):
        d = bolt.read_distance()
        readings.append(d)
        print(f"  distance: {d} cm")
        time.sleep(0.5)
    valid = [d for d in readings if d > 0]
    return len(valid) >= 5 and max(valid) - min(valid) > 5


def touch():
    print("  Touch the touch sensor a few times in the next 10 seconds.")
    end = time.time() + 10
    while time.time() < end:
        state = bolt.dual_touch.read()
        if state != "N":
            print(f"  touch detected: {state}")
            return True
        time.sleep(0.1)
    return False


def sound_direction():
    print("  Clap loudly near the sound sensor in the next 10 seconds.")
    end = time.time() + 10
    while time.time() < end:
        if bolt.ears.isdetected():
            print(f"  sound from {bolt.ears.read()} degrees")
            return True
        time.sleep(0.05)
    return False


def imu():
    print("  Tilt the IMU board slowly for 5 seconds.")
    samples = []
    for _ in range(25):
        samples.append(list(bolt.accData))
        time.sleep(0.2)
    print(f"  first: {samples[0]}  last: {samples[-1]}")
    spread = max(max(s[i] for s in samples) - min(s[i] for s in samples) for i in range(3))
    return spread > 2000


def camera():
    out = subprocess.run(["rpicam-still", "-n", "-t", "1000", "-o", "/tmp/bolt_test.jpg"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        print(f"  {out.stderr.strip().splitlines()[-1] if out.stderr else 'camera failed'}")
        return False
    print("  Photo saved to /tmp/bolt_test.jpg")
    return True


TESTS = {
    "i2c": ("I2C bus", i2c),
    "battery": ("Battery", battery),
    "speaker": ("Speaker", speaker),
    "leds": ("LED strip", leds),
    "ultrasonic": ("Ultrasonic", ultrasonic),
    "touch": ("Touch", touch),
    "sound": ("Sound direction", sound_direction),
    "imu": ("IMU (motion sensor)", imu),
    "camera": ("Camera", camera),
}
# These talk to the part directly, without starting the whole dog
NO_DOG = {"i2c", "battery", "camera"}

args = sys.argv[1:]
if args[:1] == ["servo"]:
    if len(args) != 2 or not args[1].isdigit() or not 0 <= int(args[1]) <= 11:
        sys.exit("Usage: sudo python3 bench_test.py servo <port 0-11>")
    port = int(args[1])
    run(f"Servo P{port}", lambda: servo(port))
    sys.exit(0 if all(results.values()) else 1)

chosen = args or list(TESTS)
unknown = [c for c in chosen if c not in TESTS]
if unknown:
    sys.exit(f"Unknown test: {', '.join(unknown)}. Choose from: {', '.join(TESTS)}, servo <port>")

for key in [c for c in chosen if c in NO_DOG]:
    run(*TESTS[key])

dog_tests = [c for c in chosen if c not in NO_DOG]
if dog_tests:
    from pidog import Pidog
    bolt = Pidog()
    try:
        for key in dog_tests:
            run(*TESTS[key])
    finally:
        bolt.close()

print("\n=== Summary ===")
for name, ok in results.items():
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
