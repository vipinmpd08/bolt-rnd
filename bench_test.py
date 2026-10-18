#!/usr/bin/env python3
"""Bench test for Bolt: checks every sensor before assembly.

Plug a sensor into the Robot HAT on the table, switch the battery on, then test it on its own:
    sudo python3 bench_test.py touch

Tests: speaker, leds, ultrasonic, touch, sound, imu, camera.
Run with no name to test everything in one go:
    sudo python3 bench_test.py

Each test tells you what to do (wave a hand, touch, clap...) and prints PASS or FAIL.
Servos are tested separately during zeroing (servo_zeroing.py).
"""

import subprocess
import sys
import time

from pidog import Pidog

results = {}


def run(name, test):
    print(f"\n=== {name} ===")
    try:
        results[name] = bool(test())
    except Exception as e:
        print(f"  error: {e}")
        results[name] = False
    print("  PASS" if results[name] else "  FAIL")


def speaker():
    print("  You should hear a bark.")
    bolt.speak_block("single_bark_1", volume=80)
    return input("  Did you hear it? (y/n) ").strip().lower().startswith("y")


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
    "speaker": ("Speaker", speaker),
    "leds": ("LED strip", leds),
    "ultrasonic": ("Ultrasonic", ultrasonic),
    "touch": ("Touch", touch),
    "sound": ("Sound direction", sound_direction),
    "imu": ("IMU (motion sensor)", imu),
    "camera": ("Camera", camera),
}

chosen = sys.argv[1:] or list(TESTS)
unknown = [c for c in chosen if c not in TESTS]
if unknown:
    sys.exit(f"Unknown test: {', '.join(unknown)}. Choose from: {', '.join(TESTS)}")

needs_dog = any(c != "camera" for c in chosen)
bolt = Pidog() if needs_dog else None
try:
    for key in chosen:
        if key != "camera":
            run(*TESTS[key])
finally:
    if bolt:
        bolt.close()

if "camera" in chosen:
    run(*TESTS["camera"])

print("\n=== Summary ===")
for name, ok in results.items():
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
