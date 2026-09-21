from pathlib import Path
import mujoco


MODEL_PATH = Path("simulation/models/03_pendulum.xml")

model = mujoco.MjModel.from_xml_path(str(MODEL_PATH))
data = mujoco.MjData(model)

data.qpos[0] = 0.5
data.qvel[0] = 0.0

mujoco.mj_forward(model, data)

print("qpos         =", data.qpos)
print("qvel         =", data.qvel)
print("qacc         =", data.qacc)
print("qfrc_bias    =", data.qfrc_bias)
print("qfrc_passive =", data.qfrc_passive)
print("nefc         =", data.nefc)
print("gravity      =", model.opt.gravity)