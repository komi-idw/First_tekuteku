from pathlib import Path
import time

import mujoco
import mujoco.viewer


MODEL_PATH = Path("simulation/models/02_free_body.xml")

model = mujoco.MjModel.from_xml_path(str(MODEL_PATH))
data = mujoco.MjData(model)

print(f"timestep : {model.opt.timestep} s")
print(f"nbody    : {model.nbody}")
print(f"ngeom    : {model.ngeom}")
print(f"nq       : {model.nq}")
print(f"nv       : {model.nv}")

with mujoco.viewer.launch_passive(
    model,
    data,
    show_left_ui=False,
    show_right_ui=False,
) as viewer:

    # Camera
    viewer.cam.lookat[:] = [0.0, 0.5, 0.5]
    viewer.cam.distance = 2.5
    viewer.cam.azimuth = 90
    viewer.cam.elevation = -10

    next_print_time = 0.0

    while viewer.is_running():
        mujoco.mj_step(model, data)

                # 0.1 sごとに状態を表示
        if data.time >= next_print_time:
            print(
                f"t={data.time:5.2f} s  "
                f"z={data.qpos[2]:7.4f} m  "
                f"vz={data.qvel[2]:7.4f} m/s"
            )
            next_print_time += 0.1

        viewer.sync()

        # わざとスロー再生
        time.sleep(model.opt.timestep)