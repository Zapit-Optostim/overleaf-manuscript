import zapit_python_bridge.bridge as zpb
from time import sleep

hZP = zpb.bridge()
hZP.send_samples(conditionNum=-1, hardwareTriggered=False)
sleep(0.75)
hZP.stop_opto_stim()
sleep(0.5)
