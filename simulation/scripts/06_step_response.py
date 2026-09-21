from pathlib import Path
import csv
import math

import matplotlib.pyplot as plt
import mujoco
import numpy as np


MODEL_PATH = Path("simulation/models/05_pd_servo.xml")

OUTPUT_DIR = Path("simulation/results/step_response")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = OUTPUT_DIR / "step_response.csv"
PLOT_PATH = OUTPUT_DIR / "step_response.png"


# --------------------------------------------------
# Simulation setup
# --------------------------------------------------

model = mujoco.MjModel.from_xml_path(str(MODEL_PATH))
data = mujoco.MjData(model)

data.qpos[0] = 0.0
data.qvel[0] = 0.0
mujoco.mj_forward(model, data)


# --------------------------------------------------
# Controller parameters
# --------------------------------------------------

Kp = 10.0
Kd = 2.0

step_time = 0.5
q_initial = 0.0
q_target_final = math.radians(30.0)

simulation_duration = 3.0


# --------------------------------------------------
# Logging
# --------------------------------------------------

time_history = []
target_history = []
q_history = []
dq_history = []
tau_history = []


while data.time < simulation_duration:

    t = data.time

    if t < step_time:
        q_target = q_initial
    else:
        q_target = q_target_final

    q = data.qpos[0]
    dq = data.qvel[0]

    tau = Kp * (q_target - q) - Kd * dq

    data.ctrl[0] = tau

    # 同一timestampにおけるstate / commandを保存
    time_history.append(t)
    target_history.append(q_target)
    q_history.append(q)
    dq_history.append(dq)
    tau_history.append(tau)

    mujoco.mj_step(model, data)


# NumPy arrays
time_history = np.asarray(time_history)
target_history = np.asarray(target_history)
q_history = np.asarray(q_history)
dq_history = np.asarray(dq_history)
tau_history = np.asarray(tau_history)


# --------------------------------------------------
# CSV
# --------------------------------------------------

with CSV_PATH.open("w", newline="") as f:
    writer = csv.writer(f)

    writer.writerow([
        "time_s",
        "q_target_rad",
        "q_rad",
        "dq_rad_per_s",
        "tau_Nm",
    ])

    writer.writerows(
        zip(
            time_history,
            target_history,
            q_history,
            dq_history,
            tau_history,
        )
    )


# --------------------------------------------------
# Step response metrics
# --------------------------------------------------

mask = time_history >= step_time

t_step = time_history[mask] - step_time
q_step = q_history[mask]

delta_q = q_target_final - q_initial

q_10 = q_initial + 0.1 * delta_q
q_90 = q_initial + 0.9 * delta_q


# Rise time
idx_10 = np.where(q_step >= q_10)[0]
idx_90 = np.where(q_step >= q_90)[0]

if len(idx_10) > 0 and len(idx_90) > 0:
    t_10 = t_step[idx_10[0]]
    t_90 = t_step[idx_90[0]]
    rise_time = t_90 - t_10
else:
    rise_time = np.nan


# Overshoot
q_max = np.max(q_step)

overshoot = max(
    0.0,
    (q_max - q_target_final) / abs(delta_q) * 100.0
)


# Settling time: ±2 %
settling_band = 0.02 * abs(delta_q)

settling_time = np.nan

for i in range(len(q_step)):

    remaining_error = np.abs(
        q_step[i:] - q_target_final
    )

    if np.all(remaining_error <= settling_band):
        settling_time = t_step[i]
        break


# Steady-state error: final 0.5 s average
steady_mask = time_history >= simulation_duration - 0.5

q_steady = np.mean(q_history[steady_mask])

steady_state_error = q_target_final - q_steady


# --------------------------------------------------
# Results
# --------------------------------------------------

print()
print("=== Step Response Metrics ===")
print(f"Kp                  : {Kp}")
print(f"Kd                  : {Kd}")
print(f"Target              : {q_target_final:.6f} rad")
print(f"Target              : {math.degrees(q_target_final):.2f} deg")
print(f"Rise time           : {rise_time:.4f} s")
print(f"Overshoot           : {overshoot:.2f} %")
print(f"Settling time       : {settling_time:.4f} s")
print(f"Steady-state error  : {steady_state_error:.6f} rad")
print(
    f"Steady-state error  : "
    f"{math.degrees(steady_state_error):.4f} deg"
)


# --------------------------------------------------
# Plot
# --------------------------------------------------

fig, axes = plt.subplots(
    3,
    1,
    figsize=(8, 9),
    sharex=True,
)

axes[0].plot(
    time_history,
    target_history,
    "--",
    label="Target",
)

axes[0].plot(
    time_history,
    q_history,
    label="Position",
)

axes[0].set_ylabel("Position [rad]")
axes[0].grid()
axes[0].legend()


axes[1].plot(
    time_history,
    dq_history,
)

axes[1].set_ylabel("Velocity [rad/s]")
axes[1].grid()


axes[2].plot(
    time_history,
    tau_history,
)

axes[2].set_ylabel("Torque [N m]")
axes[2].set_xlabel("Time [s]")
axes[2].grid()


plt.tight_layout()
plt.savefig(PLOT_PATH, dpi=150)
plt.show()


print()
print(f"CSV saved : {CSV_PATH}")
print(f"Plot saved: {PLOT_PATH}")