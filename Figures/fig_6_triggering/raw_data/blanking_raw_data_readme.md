
Data acquired to demonstrate accuracy of blanking relative to beam position



## Experimental Setup

Beam moving back and forth by 10 mm along one axis over the surafce of a ThorLab's photodiode. The setup uses ScannerMax galvos. The beam is blanked during the motion epoch (which is about 0.4 ms). We the same NI DAQ to acquire the galvo command signal, the position feedback signal from the galvo, and the photodiode. The idea being that we can overlay the galvo angular positio and the photodiode trace and demonstrate that the beam is off during the period the scanner is moving. We acquire some 300 or so back and forth cycles of the beam so can plot the beam going left to right and also right to left. 





## Data format

The  `.bin` file is read by the `readAndPlot.m` function. Data are interleaved, so they go [control0,feedback0,photodiode0,control1,....]

There is an example showing how to plot this in `readAndPlot.m` and also the main figure plotting code makes it clear. 

Data were acquired at 10,000 samples per second. 

