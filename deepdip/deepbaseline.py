from baselines.common import plot_util as pu

import matplotlib.pyplot as plt
import numpy as np

results = pu.load_results('./deepdip-results/test_run')

r = results[0]
#plt.plot(np.cumsum(r.monitor.l), r.monitor.r)#pu.smooth(r.monitor.r, radius=10))
#plt.plot(np.cumsum(r.monitor.l), pu.smooth(r.monitor.r, radius=5))
pu.plot_results(results, average_group=True)

plt.savefig('deepdip.png')
plt.show()

