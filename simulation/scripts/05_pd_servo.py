from pathlib import Path

import mujoco


MODEL_PATH = Path("simulation/models/05_pd_servo.xml")

model = mujoco.MjModel.from_xml_path(str(MODEL_PATH))
data = mujoco.MjData(model)


# Initial state
data.qpos[0] = 0.0
data.qvel[0] = 0.0
mujoco.mj_forward(model, data)


# PD gains
Kp = 10.0
Kd = 2.0

# Target position
q_target = 0.5  # [rad]

simulation_duration = 3.0
next_print_time = 0.0


while data.time < simulation_duration:

    q = data.qpos[0]
    dq = data.qvel[0]

    # PD controller
    tau = Kp * (q_target - q) - Kd * dq

    # Send torque through MuJoCo actuator
    data.ctrl[0] = tau

    mujoco.mj_step(model, data)

    if data.time >= next_print_time:
        print(
            f"t={data.time:5.2f} s  "
            f"target={q_target:+.3f} rad  "
            f"q={q:+.3f} rad  "
            f"dq={dq:+.3f} rad/s  "
            f"tau={tau:+.3f} N m"
        )

        next_print_time += 0.1