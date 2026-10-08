# Presentation script: AnnoBot experiment results

Target length: about 12-15 minutes (22 slides, 7 of them are quick demo screenshots).
Numbers come from the production API (3-day live run, 28-30/09/2026).

---

## Slide 1: Title
Good morning, everyone. Today we report the first results of our two live experiments: the Kitchen and the Meeting Room. We will go through the setup, how we detect cycles, what we actually collected over three days, and what is still missing.

## Slide 2: Recap of the previous meeting
Quick recap of what we agreed last time.
First, the experiments: we kept the Meeting Room with the TV, and we added a Kitchen experiment with the fridge and the microwave.
Second, we changed two terms. A **Fact** is now called a **Case**: a collection of sensor observations, contextual information, and semantic annotations that are relevant to the inquiry goal.
And **signature extraction** is now called **cycle detection**: a rule that scans the sensor trace and returns the start and end time of an appliance cycle or service episode.

## Slide 3: Experiment setup
Both experiments run for one month, from 28 September to 28 October. Today we only have the first three days.
The ask window is 24/7. That is only for testing. In real life it would be something like 9 am to 9 pm.
Each experiment can ask at most 10 questions per day, to keep the burden on occupants low.
The IL timestep is 60 minutes for the Kitchen and 30 minutes for the Meeting Room.

## Slide 4: Demo, experiment list
This is how the two experiments look in the web interface: title, how often it asks, the daily budget and the ask window.

## Slide 5: Inquiries
Each experiment contains inquiries. An inquiry has a question, a sensor set, a detection rule, and an annotation scope.
We have four inquiries.
The **fridge** asks how regular the compressor cycle is and how much energy each cycle uses. It needs no annotation, so we call it annotation-free.
The **microwave** asks when it is used and what for. Here the `what` field is required.
The **session** inquiry asks when the meeting room is used and for how long. It uses the TV plug plus temperature and humidity, and it requires `who` and `what`.
The **comfort** inquiry asks whether temperature and humidity stay in the comfort band during meetings. It uses a `climate_observation` rule.

## Slide 6: Inquiry goals and indicators
Every inquiry also has a goal and a set of indicators.
For the fridge, the goal is to confirm that the detector draws consistent on/off boundaries over many repetitions. It is not anomaly detection.
For the microwave, we want the detector to cope with a sparse, short, noisy signal, and to sort each burst into one of four uses.
For the session inquiry, we want to measure real occupancy of the room instead of inferring it from the TV alone.
For comfort, we want to trade comfort against energy and surface an AC left running when nobody is in the room.
The indicators are what we compute for each case, for example energy, duration, mean power and peak power.

## Slide 7: Demo, meeting-room inquiries
Here are the two meeting-room inquiries in the web interface, with their sensors, detection rule, and the fields the occupant must answer.

## Slide 8: Cycle detection, adaptive ON/OFF thresholds
Now the method. The goal is to find the start and end of each appliance cycle from raw power, without thresholds tuned by hand.
We learn the thresholds from the data. We look for the power level that best separates the OFF, or standby, readings from the ON readings. We do this on the logarithm of power, because power is multiplicative and its histogram is skewed to the right, so a linear scale misses low-power states.
We use two thresholds, one to switch ON and a lower one to switch OFF. This is hysteresis, and it stops a cycle from flickering around a single value.
Then we clean up: we drop cycles that are too short and merge short pauses.
Why not the median plus k times MAD? That approach assumes the OFF state dominates. A fridge is ON about 70% of the time, so the median lands inside the ON state and cycles are missed.

## Slide 9: Learned thresholds
These are the thresholds we ended up with.
Fridge: about 9.2 W to turn on and 5.2 W to turn off, no gap merging, duration between 3 and 120 minutes.
Microwave: about 24 W on and 10.8 W off, gaps up to 2 minutes are merged, duration 1 to 15 minutes.
The TV uses a fixed profile from the UK-DALE dataset: 10 W on, about 5.2 W off, gaps up to 5 minutes, and at least 5 minutes long.
The learned values are re-estimated on every run, so they move slightly. For example, the fridge turn-on threshold stays between 9.1 and 9.4 W.

## Slide 10: Demo, thresholds recorded with a case
In the interface, every case records the thresholds that bounded it. This is the TV session on 30 September: turn-on 10 W, turn-off 5.2 W, maximum gap 5 minutes, minimum duration 5 minutes. The interface also tells us when the detection rule was updated at that cycle, and shows the measured peak and integrated energy.

## Slide 11: Overview of the 3-day run
Here is the overall result.
The fridge produced 48 cases, all annotation-free, with a median duration of 54 minutes and about 39 Wh per cycle.
The microwave produced 5 cases, all annotated, with an average of 7 minutes and about 99 Wh per use.
The TV session produced 3 cases, all annotated, about 19 minutes and about 41 Wh per session.
The comfort inquiry produced no cases yet, because we have no detector for it.
Mean power, peak and energy come from the integrated raw events.

## Slide 12: Demo, power dashboard
This dashboard shows the power consumption of all eleven devices over the last 24 hours, in 15-minute averages. It gives context: you can see the day starting around 9 am and the peak around lunchtime.

## Slide 13: Meeting Room, lunch-break routine
The most interesting finding is in the meeting room. On three consecutive days, between 11:35 and 12:15, occupants turned on the TV to watch YouTube while eating lunch.
The sessions last between 16 and 23 minutes, with peaks around 130 to 140 W and between 35 and 52 Wh of energy.
The occupants told us who was there, from "many people" to "6 people", and what they were doing: eating and watching TV or YouTube.
This is exactly the kind of routine the inquiry was designed to reveal.

## Slide 14: Demo, extracted cases
Here are the three extracted cases in the web interface, on a three-day timeline. All three are annotated, and the most recent one is flagged because its detection rule was updated.

## Slide 15: Demo, real-life event
And this is the real event behind those numbers: people having lunch in the meeting room with the TV on.

## Slide 16: Demo, annotation chat
This is how the annotation happens. The bot notices the TV activity between 11:36 and 11:52 on 29 September and asks who was involved. The occupant answers "6 people". The bot then asks what happened, and the answer is "people eating and watching TV". Two required fields, and the case is complete.

## Slide 17: Kitchen, microwave
In the kitchen, the microwave was used five times. All five were annotated as reheating a meal.
The peak power is always around 1.2 kW.
Durations range from 2 to 15 minutes, and the energy from 33 to 211 Wh, roughly following the duration.
One point to be honest about: all five labels are the same, so we cannot yet judge how well the four categories can be told apart.

## Slide 18: Kitchen, fridge
The fridge is our annotation-free case. We detected 48 cycles in about 2.7 days, roughly 18 per day, without asking the occupant anything.
For the 45 regular cycles, the duration is between 34 and 93 minutes with a median of 54, mean power 39 to 103 W, and 28 to 79 Wh per cycle.
Three cycles are outliers, between 119 and 305 minutes, and carry the duration-over-max flag. We have not investigated their cause yet.

## Slide 19: Limitations
We see five limitations.
One: we do not yet do timestep resampling and discretization. Cases are not projected onto a 15, 30 or 60-minute grid and binned into low, medium and high, so the matrix that feeds the interactive-learning trigger is not built.
Two: the engine only supports appliance power cycles, so the comfort inquiry produced no cases.
Three: there is no cooperative quality control. Users cannot confirm, edit or reject labels inferred by the bot.
Four: we have no occupancy sensors, so `who` depends on what people type.
Five: the abnormally long fridge cycles are not yet split or explained.

## Slide 20: Future work
Each limitation has a next step.
Timestep discretization: resample cases onto a standard grid and bin values into low, medium and high for the interactive-learning trigger.
Climate binding: attach temperature and humidity to each TV interval and add comfort-band rules, so the comfort inquiry can produce cases.
Cooperative QC: a web interface to confirm, edit, reject or defer labels filled in by the bot.
Occupancy sensing: PIR, door contacts and CO2 to estimate the number of people automatically.

## Slide 21: Pipeline and roadmap
Putting it together, the pipeline is: raw sensor data, cycle detection, a case with its start and end time, then timestep resampling and discretization, then the interactive-learning trigger and quality control.
The first two steps are done. The next milestone is timestep resampling and discretization.
Once a case exists, temporal resampling projects cases of different lengths onto a standard time grid to build the analysis matrix, and semantic binning turns numeric values into low, medium and high.
The reason is that the interactive-learning trigger, which uses neighbourhood density, needs time-aligned feature vectors to compare cases and decide whether it should ask the user.

## Slide 22: References
These are the references. Thank you for listening, and we are happy to take questions.

---

## Likely questions (short answers)
- **Why these thresholds instead of fixed ones?** Different appliances have very different power levels, and standby can be as high as a few watts, so learning them from each device's own data avoids manual tuning.
- **Why does the fridge have outliers?** We do not know yet. Possible explanations are two cycles merged into one or a door left open, but we have not checked.
- **Only three sessions, is that enough?** No. This is the first three days of a one-month experiment, so we treat it as a feasibility check, not a conclusion.
- **Why is the microwave always "reheating a meal"?** It is what the occupants actually did in these three days. We need more varied use to test the four categories.
- **Why is the comfort inquiry empty?** Temperature and humidity are continuous background signals with no clear ON/OFF pulse, so the current power-cycle detector does not apply. It needs its own detector, which is part of the future work.
