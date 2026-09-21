from pathlib import Path
import csv

import matplotlib.pyplot as plt
import mujoco


MODEL_PATH = Path("simulation/models/02_free_body.xml")
OUTPUT_DIR = Path("simulation/results/free_body")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = OUTPUT_DIR / "free_fall.csv"
PLOT_PATH = OUTPUT_DIR / "free_fall.png"


model = mujoco.MjModel.from_xml_path(str(MODEL_PATH))
data = mujoco.MjData(model)

simulation_duration = 1.0

time_history = []
z_history = []
vz_history = []

while data.time < simulation_duration:
    time_history.append(data.time)
    z_history.append(data.qpos[2])
    vz_history.append(data.qvel[2])

    mujoco.mj_step(model, data)


# CSV
with CSV_PATH.open("w", newline="") as f:
    writer = csv.writer(f)

    writer.writerow([
        "time_s",
        "z_m",
        "vz_m_per_s",
    ])

    writer.writerows(
        zip(
            time_history,
            z_history,
            vz_history,
        )
    )


# Plot: position
plt.figure()

plt.plot(
    time_history,
    z_history,
)

plt.xlabel("Time [s]")
plt.ylabel("Z position [m]")
plt.grid()

plt.savefig(PLOT_PATH)
plt.show()


print(f"CSV saved : {CSV_PATH}")
print(f"Plot saved: {PLOT_PATH}")