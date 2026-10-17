#!/usr/bin/env python3
"""Bolt's first moves: stand, wag, bark, lie down.

Run on the Pi with the dog assembled and the battery switched on:
    sudo python3 hello_bolt.py
"""

from pidog import Pidog

bolt = Pidog()

try:
    print("Bolt, stand!")
    bolt.do_action("stand", speed=60)
    bolt.wait_all_done()

    print("Wag your tail!")
    bolt.rgb_strip.set_mode("breath", "cyan", bps=1)
    bolt.do_action("wag_tail", step_count=10, speed=80)
    bolt.wait_all_done()

    print("Speak!")
    bolt.speak_block("single_bark_1", volume=80)

    print("Lie down. Good boy!")
    bolt.do_action("lie", speed=50)
    bolt.wait_all_done()

except KeyboardInterrupt:
    pass
finally:
    bolt.close()
