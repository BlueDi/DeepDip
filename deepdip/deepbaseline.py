from baselines.common import plot_util as pu

import matplotlib.pyplot as plt
import numpy as np

results = pu.load_results('./deepdip-results')

r = results[0]
plt.plot(np.cumsum(r.monitor.l), r.monitor.r)#pu.smooth(r.monitor.r, radius=10))

plt.savefig('deepdip.png')
plt.show()

