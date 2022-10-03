import pandas as pd
import matplotlib.pyplot as plt
class TO_REF():
    def __init__(self):
        self.data = pd.read_csv('../../../../data/performance/wilabada/20190101_MPH8321_1215_outb.sur', usecols=[1, 5, 8, 23, 28, 33, 34], delimiter=";", header=None)
        self.data.columns = ["Callsign", "FL", "TAS", "cROCD", "ALT", "LAT", "LON"]
        self.FL = self.data.iloc[:,1].values
        self.TAS = self.data.iloc[:,2].values
        self.cROCD = self.data.iloc[:,3].values
        self.ALT = self.data.iloc[:,4].values
        self.LAT = self.data.iloc[:,5].values
        self.LON = self.data.iloc[:,6].values

        # self.callsign =
        # print(self.data)

# plt.plot([i for i in range(len(TO_REF().FL))], TO_REF().cROCD)
plt.plot(TO_REF().FL, TO_REF().cROCD)
plt.show()