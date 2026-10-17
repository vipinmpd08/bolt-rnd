# Bolt feature roadmap 🐕⚡

Built in layers. Each phase works on its own, so Bolt gets smarter step by step.

## Phase 1: Body (first week after assembly)
- [ ] **First moves**: stand, sit, lie down, wag, bark (`hello_bolt.py`)
- [ ] **Walk and turn** on command from the laptop keyboard
- [ ] **Step calibration**: measure steps per metre and degrees per turn on your floor
- [ ] **Moods on the LED strip**: breathing blue when calm, red when alert, pink when happy

## Phase 2: Reflexes (run on the Pi, no AI, instant)
- [ ] **Obstacle stop**: halts before walls using the ultrasonic sensor
- [ ] **Head pat**: touch sensor makes him wag and lean into your hand
- [ ] **Picked up / fallen over**: the motion sensor notices, he gets back up or "complains"
- [ ] **Turn to sound**: looks toward a clap or a voice (sound direction sensor)
- [ ] **Low battery**: gets sleepy, lies down and asks to be charged
- [ ] **Emergency stop**: "Bolt, stop!" or one key on the laptop freezes him instantly

## Phase 3: Voice
- [ ] **Wake word "Bolt"**: he only listens after hearing his name
- [ ] **Speech to text** on the Pi
- [ ] **Talks back** in his own voice (Piper text-to-speech)
- [ ] **Voice commands**: "Bolt, sit", "Bolt, come here", "Bolt, dance"
- [ ] **Chat**: ask him anything, he answers in character as a cheeky dog

## Phase 4: Eyes
- [ ] **Face spotting**: notices when someone is in front of him
- [ ] **Follow me**: tracks a face or a red ball and walks after it
- [ ] **Know the family**: recognises your face and greets you by name
- [ ] **"What do you see?"**: sends a photo to a vision AI and describes it

## Phase 5: Brain (the agentic part)
- [ ] **Multi-step missions**: "turn right, walk 1 metre, if someone is sitting there say hi"
- [ ] **Re-planning**: if blocked, he finds another way or tells you what happened
- [ ] **Room map**: learns places from where he has walked, so "go to the sofa" works
- [ ] **Swappable AI**: Grok free tier first, Claude later, one setting in `.env`

## Phase 6: Feelings and memory (the "real animal" part)
- [ ] **Drives**: energy, happiness, curiosity, boredom rise and fall over time
- [ ] **Acts on his own**: explores when bored, naps when tired, seeks you when lonely
- [ ] **Idle life and day rhythm**: sniffs, stretches and wanders; sleepy at night, lively in the morning
- [ ] **Memory**: remembers names, tricks you taught him and what happened today
- [ ] **Personality**: grows over days based on how you treat him
- [ ] **Daily diary**: tells you about his day in the evening

## Phase 7: Fun extras
- [ ] **Learn tricks**: teach a new move by voice ("Bolt, this is called spin")
- [ ] **Guard mode**: patrols and barks if someone unknown appears, sends you a photo
- [ ] **Phone remote**: control and watch his camera from your phone
- [ ] **Games**: fetch the ball, hide and seek, follow the leader
- [ ] **Photo mode**: "Bolt, take a picture of me"

## Honest limits
- Distance and turns are approximate (about 10 to 20% off) since he walks rather than rolls.
- The Pi 3B+ handles reflexes and simple vision; heavy thinking happens in the cloud.
- He won't truly think, but with drives and memory he will act convincingly like a pet.
