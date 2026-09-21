from pathlib import Path
import time

import mujoco
import mujoco.viewer

MODEL_PATH = Path("simulation/models/04_torque_input.xml")

model = mujoco.MjModel.from_xml_path(str(MODEL_PATH))
data = mujoco.MjData(model)

# 初期状態
data.qpos[0] = 0.0
data.qvel[0] = 0.0

mujoco.mj_forward(model, data)

# 与えるトルク
tau = -1.0  # [N m]

simulation_duration = 1.0
next_print_time = 0.0

while data.time < simulation_duration:

    # generalized coordinate q[0] に直接トルクを加える
    data.qfrc_applied[0] = tau

    mujoco.mj_step(model, data)

    if data.time >= next_print_time:
        print(
            f"t={data.time:5.2f} s  "
            f"tau={tau:+.2f} N m  "
            f"q={data.qpos[0]:+.4f} rad  "
            f"dq={data.qvel[0]:+.4f} rad/s  "
            f"ddq={data.qacc[0]:+.4f} rad/s^2"
        )

        next_print_time += 0.1

with mujoco.viewer.launch_passive(
    model,
    data,
    show_left_ui=False,
    show_right_ui=False,
) as viewer:

    viewer.cam.lookat[:] = [0.0, 0.0, 1.0]
    viewer.cam.distance = 3.0
    viewer.cam.azimuth = 90
    viewer.cam.elevation = 0

    while viewer.is_running():

        mujoco.mj_step(model, data)

        viewer.sync()

        time.sleep(model.opt.timestep)