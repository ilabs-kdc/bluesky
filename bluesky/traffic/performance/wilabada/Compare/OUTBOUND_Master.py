from OUTBOUND_FUNCS import *
from EEI import EEI

data = SURR_dicts(r"C:\Users\LVNL_ILAB3\PycharmProjects\bluesky\bluesky\traffic\performance\wilabada\Compare\Surr", "artas.fields")

callsign = "EZY23KH"
# for i in data[callsign]:
#     print(i, data[callsign][i])


EEI = EEI()

aircraft = "A320"

fig = plt.gcf()
fig.set_size_inches(18.5, 10.5)
plt.title(aircraft)

FL = np.array(EEI.speedsFL[aircraft])
SP = np.array(EEI.speedsIAS[aircraft])

plt.plot(FL[FL <= 100], SP[FL <= 100], label = "Data")
plt.plot(np.array(data[callsign]["fl"])[np.array(data[callsign]["fl"])<100], np.array(data[callsign]["ias"][np.array(data[callsign]["fl"])<100]), label=callsign)

SP_i = []
FL_i = []

for i in range(0, 101):
    SP_i.append(EEI.speedfuncs[aircraft](i))
    FL_i.append(i)
plt.plot(FL_i, SP_i, label = "Interpolate")
plt.xticks(np.arange(0, 105, step=5))
plt.grid()
plt.legend()
plt.show()