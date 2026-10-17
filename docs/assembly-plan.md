# Bolt assembly plan (PiDog V1)

Seven short sessions. Tick them off as you go. Always follow the **printed manual** first; SunFounder says the videos can differ slightly.

- Video 1, body and four legs: https://www.youtube.com/watch?v=PTo6smSIlDY
- Video 2, head and calibration: https://www.youtube.com/watch?v=witCWeoHTdk

## Before every servo (V1 rule)

Zero it first. With the Pi powered from the Robot HAT battery:

```
cd ~/pidog/examples
sudo python3 servo_zeroing.py
```

Plug the servo into **P11**. The shaft snaps to 0°. Fit it into the body as the manual shows, then unplug it and zero the next one. Don't turn the shaft by hand after zeroing.

## Sessions

- [ ] **0. Prep (about 20 min).** Check every part against the manual's parts list. Sort the screws by size into a tray. Put the battery on charge.
- [ ] **1. Body frame (video 1).** Build the main body. Mount the Pi and Robot HAT with just enough screws to hold them, so the Pi is easy to take out later. Connect the battery and check the Pi boots from it.
- [ ] **2. Front legs (video 1).** Two legs, two servos each. Zero each servo just before fitting it.
- [ ] **3. Back legs (video 1).** Same as the front legs. After this, Bolt has a body and four legs.
- [ ] **4. Head and tail (video 2).** Neck servos, camera, ultrasonic sensor, touch sensor, LED strip and the tail servo. Zero every servo first.
- [ ] **5. Wiring.** Plug each servo into the port shown in the manual. The camera ribbon goes into the Pi's **CAMERA** port (not DISPLAY). Tidy the cables so no leg can catch them.
- [ ] **6. Calibrate and first moves (video 2).** Put Bolt on a flat table and run `sudo python3 0_calibration.py` in `~/pidog/examples` with the acrylic ruler. Then run `sudo python3 ~/bolt-rnd/hello_bolt.py`. 🎉

## Port reference (from the pidog library)

| Part | Robot HAT ports |
| --- | --- |
| Legs (8 servos) | P0, P1, P2, P3, P7, P8, P10, P11 |
| Head (3 servos) | P4, P5, P6 |
| Tail (1 servo) | P9 |

The manual shows which leg servo goes in which of those ports.
