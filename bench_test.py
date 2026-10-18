#!/usr/bin/env python3
"""Bench test for Bolt: checks every sensor before assembly.

Plug a sensor into the Robot HAT on the table, switch the battery on, then test it on its own:
    python3 bench_test.py touch

Tests: i2c, battery, speaker, leds, ultrasonic, touch, sound, imu, mic, camera.
Test one loose servo plugged into port P0 to P11 (turns +30, then -30, then stops at 0, which zeroes it):
    python3 bench_test.py servo 3
Run with no name to test every sensor in one go:
    python3 bench_test.py

Each test tells you what to do (wave a hand, touch, clap...) and prints PASS or FAIL.
Every test talks to its part directly, so servos never move except in the servo test.
Don't use sudo: it clashes with the Pi's sound system.
The V1 Robot HAT has no microphone; the mic test uses the kit's USB mic.
"""

import array
import os
import subprocess
import sys
import time
import wave

results = {}


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
    for angle, label in ((30, "+30 degrees"), (-30, "-30 degrees"), (0, "0 (zeroed)")):
        print(f"  P{port} -> {label}")
        s.angle(angle)
        time.sleep(1)
    return input("  Did it move smoothly? (y/n) ").strip().lower().startswith("y")


def speaker():
    # robot_hat's player directly: pidog's speak() runs sudo and asks for a password
    from robot_hat import Music
    music = Music()
    sounds = os.path.expanduser("~/pidog/sounds/")
    print("  You should hear 5 long barks.")
    for i in range(5):
        print(f"  bark {i + 1}")
        # Two barks back to back make one longer bark
        for name in ("single_bark_1", "single_bark_2"):
            music.sound_play(f"{sounds}{name}.mp3", 100)
        time.sleep(0.5)
    return input("  Did you hear all 5? (y/n) ").strip().lower().startswith("y")


def leds():
    from pidog.rgb_strip import RGBStrip
    strip = RGBStrip(addr=0x74, nums=11)
    colors = [("red", [255, 0, 0]), ("green", [0, 255, 0]), ("blue", [0, 0, 255]), ("white", [255, 255, 255])]
    for name, rgb in colors:
        print(f"  all 11 lights: {name}")
        strip.display([rgb] * 11)
        time.sleep(2)
    strip.display([[0, 0, 0]] * 11)
    return input("  Did all 11 light up in every colour? (y/n) ").strip().lower().startswith("y")


def ultrasonic():
    from robot_hat import Pin, Ultrasonic
    sensor = Ultrasonic(Pin("D1"), Pin("D0"), timeout=0.017)
    print("  Move your hand closer to and further from the sensor for 5 seconds.")
    readings = []
    for _ in range(10):
        d = sensor.read()
        readings.append(d)
        print(f"  distance: {d} cm")
        time.sleep(0.5)
    valid = [d for d in readings if d > 0]
    return len(valid) >= 5 and max(valid) - min(valid) > 5


def touch():
    from pidog.dual_touch import DualTouch
    sensor = DualTouch("D2", "D3")
    print("  Touch the touch sensor a few times in the next 10 seconds.")
    end = time.time() + 10
    while time.time() < end:
        state = sensor.read()
        if state != "N":
            print(f"  touch detected: {state}")
            return True
        time.sleep(0.1)
    return False


def sound_direction():
    from pidog.sound_direction import SoundDirection
    ears = SoundDirection()
    print("  Clap loudly near the sound sensor in the next 10 seconds.")
    try:
        end = time.time() + 10
        while time.time() < end:
            if ears.isdetected():
                print(f"  sound from {ears.read()} degrees")
                return True
            time.sleep(0.05)
        return False
    finally:
        ears.close()


def imu():
    from pidog.sh3001 import Sh3001
    sensor = Sh3001(db=os.path.expanduser("~/.config/pidog/pidog.conf"))
    print("  Tilt the IMU board slowly for 5 seconds.")
    samples = []
    for _ in range(25):
        samples.append(list(sensor._sh3001_getimudata()[0]))
        time.sleep(0.2)
    print(f"  first: {samples[0]}  last: {samples[-1]}")
    spread = max(max(s[i] for s in samples) - min(s[i] for s in samples) for i in range(3))
    return spread > 2000


def mic():
    out = subprocess.run(["arecord", "-l"], capture_output=True, text=True).stdout
    cards = [line for line in out.splitlines() if line.startswith("card ") and "USB" in line]
    if not cards:
        print("  No USB mic found. Plug it into a USB port on the Pi.")
        return False
    card = cards[0].split()[1].rstrip(":")
    print(f"  found: {cards[0]}")
    wav = "/tmp/bolt_mic.wav"
    print("  Talk now for 3 seconds...")
    rec = subprocess.run(["arecord", "-D", f"plughw:{card},0", "-f", "S16_LE", "-r", "16000",
                          "-c", "1", "-d", "3", "-q", wav], capture_output=True, text=True)
    if rec.returncode != 0:
        print(f"  recording failed: {rec.stderr.strip()}")
        return False
    # Loudest sample, to catch a mic that records only silence
    with wave.open(wav) as w:
        samples = array.array("h", w.readframes(w.getnframes()))
    peak = max((abs(x) for x in samples), default=0)
    print(f"  loudest sound: {peak * 100 // 32768}% of full scale")
    print("  Playing it back...")
    subprocess.run(["pw-play", wav])
    if peak < 1000:
        print("  Very quiet. Raise the mic level in alsamixer (F6, pick the USB mic, F4).")
    return input("  Did you hear your voice? (y/n) ").strip().lower().startswith("y")


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
    "mic": ("USB microphone", mic),
    "camera": ("Camera", camera),
}
args = sys.argv[1:]
if args[:1] == ["servo"]:
    if len(args) != 2 or not args[1].isdigit() or not 0 <= int(args[1]) <= 11:
        sys.exit("Usage: python3 bench_test.py servo <port 0-11>")
    port = int(args[1])
    run(f"Servo P{port}", lambda: servo(port))
    sys.exit(0 if all(results.values()) else 1)

chosen = args or list(TESTS)
unknown = [c for c in chosen if c not in TESTS]
if unknown:
    sys.exit(f"Unknown test: {', '.join(unknown)}. Choose from: {', '.join(TESTS)}, servo <port>")

for key in chosen:
    run(*TESTS[key])

print("\n=== Summary ===")
for name, ok in results.items():
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
