from pathlib import Path
import time

import mujoco
import mujoco.viewer


MODEL_PATH = Path("simulation/models/03_pendulum.xml")

model = mujoco.MjModel.from_xml_path(str(MODEL_PATH))
data = mujoco.MjData(model)

data.qpos[0] = 0.5
mujoco.mj_forward(model, data)
print("number of contacts:", data.ncon)

for i in range(data.ncon):
    contact = data.contact[i]

    geom1 = mujoco.mj_id2name(
        model,
        mujoco.mjtObj.mjOBJ_GEOM,
        contact.geom1,
    )

    geom2 = mujoco.mj_id2name(
        model,
        mujoco.mjtObj.mjOBJ_GEOM,
        contact.geom2,
    )

    print(i, geom1, geom2, contact.dist)

print(f"nq    : {model.nq}")
print(f"nv    : {model.nv}")
print(f"njnt  : {model.njnt}")
print(f"nbody : {model.nbody}")

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