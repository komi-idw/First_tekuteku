from pathlib import Path

import mujoco


MODEL_PATH = Path("simulation/models/03_pendulum.xml")

model = mujoco.MjModel.from_xml_path(str(MODEL_PATH))
data = mujoco.MjData(model)

# 28.6 deg
data.qpos[0] = 0.5
mujoco.mj_forward(model, data)

print("initial q    =", data.qpos[0])
print("initial dq   =", data.qvel[0])
print("initial qacc =", data.qacc[0])

next_print = 0.0

while data.time < 10.0:
    mujoco.mj_step(model, data)

    if data.time >= next_print:
        print(
            f"t={data.time:5.2f} "
            f"q={data.qpos[0]: .4f} rad "
            f"dq={data.qvel[0]: .4f} rad/s"
        )
        next_print += 0.1