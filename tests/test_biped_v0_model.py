"""Regression checks for models/biped_v0 (CAD-based MJCF).

Run:  uv run --extra sim python tests/test_biped_v0_model.py
      (pytest-compatible: every check is a test_* function)
"""

from __future__ import annotations

import json
from pathlib import Path

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "models" / "biped_v0"
SCENE = MODEL / "scene.xml"

JOINTS = [
    "left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee_pitch", "left_ankle_pitch",
    "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee_pitch", "right_ankle_pitch",
]


def _load():
    m = mujoco.MjModel.from_xml_path(str(SCENE))
    d = mujoco.MjData(m)
    mujoco.mj_resetDataKeyframe(m, d, m.key("home").id)
    mujoco.mj_forward(m, d)
    return m, d


def test_structure_and_ordering():
    m, _ = _load()
    assert (m.nq, m.nv, m.nu) == (17, 16, 10)
    hinge = [m.joint(i).name for i in range(m.njnt) if m.jnt_type[i] == mujoco.mjtJoint.mjJNT_HINGE]
    assert hinge == JOINTS
    assert [m.actuator(i).name for i in range(m.nu)] == JOINTS
    # qpos index of joint k = 7 + k (free joint first)
    assert [int(m.joint(j).qposadr[0]) for j in JOINTS] == list(range(7, 17))


def test_mass_matches_cad():
    m, _ = _load()
    props = json.loads((MODEL / "cad_export" / "biped_v0_v4_properties.json").read_text())
    cad_total = sum(l["mass_g"] for l in props["links"].values()) / 1000
    robot_mass = m.body_subtreemass[m.body("torso").id]
    assert abs(robot_mass - cad_total) < 1e-6, (robot_mass, cad_total)
    assert 0.6 < robot_mass < 0.7


def test_mesh_scale_and_side():
    m, d = _load()
    # torso mesh is 68.8 mm wide (CAD X) -> robot y, in metres (MuJoCo re-centres mesh_vert, so read the STL)
    raw = (MODEL / "meshes" / "torso.stl").read_bytes()
    n = int.from_bytes(raw[80:84], "little")
    v = np.frombuffer(raw, dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")], count=n, offset=84)["v"]
    ext = v.reshape(-1, 3).max(0) - v.reshape(-1, 3).min(0)
    assert abs(ext[1] - 0.0688) < 1e-3, ext
    assert d.xpos[m.body("left_foot_link").id][1] > 0.05
    assert d.xpos[m.body("right_foot_link").id][1] < -0.05


def test_home_feet_on_ground():
    m, d = _load()
    for side in ("left", "right"):
        g = m.geom(f"{side}_foot_link_collision").id
        bottom = d.geom_xpos[g][2] - m.geom_size[g][2]
        assert abs(bottom) < 5e-4, (side, bottom)
    assert d.ncon == 0  # no self-collision / penetration at home


def test_joint_positive_direction():
    """Right-hand rule about robot axes: yaw +z, roll +x, pitch +y."""
    m, d = _load()
    expect = {  # (joint, foot displacement axis, sign) for +0.2 rad
        "left_hip_pitch": (0, -1), "right_hip_pitch": (0, -1),   # leg swings backward
        "left_hip_roll": (1, +1), "right_hip_roll": (1, +1),     # foot moves to +y
        "left_knee_pitch": (0, -1), "right_knee_pitch": (0, -1),
    }
    for j, (ax, sign) in expect.items():
        side = j.split("_")[0]
        b = m.body(f"{side}_foot_link").id
        d2 = mujoco.MjData(m)
        mujoco.mj_resetDataKeyframe(m, d2, 0)
        mujoco.mj_forward(m, d2)
        p0 = d2.xpos[b].copy()
        d2.qpos[m.joint(j).qposadr] += 0.2
        mujoco.mj_forward(m, d2)
        assert np.sign((d2.xpos[b] - p0)[ax]) == sign, j


def _upright_after(m, d, ctrl, seconds, ramp=1.0):
    """Ramp ctrl linearly from 0 over `ramp` seconds, then hold."""
    steps = int(seconds / m.opt.timestep)
    for i in range(steps):
        d.ctrl[:] = ctrl * min(1.0, i * m.opt.timestep / ramp)
        mujoco.mj_step(m, d)
    z = d.xmat[m.body("torso").id].reshape(3, 3)[:, 2]
    return np.degrees(np.arccos(np.clip(z[2], -1, 1))), d.qpos[2]


def test_stands_at_home_10s():
    m, d = _load()
    tilt, h = _upright_after(m, d, np.zeros(m.nu), 10.0)
    assert tilt < 2.0 and h > 0.20, (tilt, h)
    touch = d.sensor("left_foot_touch").data[0] + d.sensor("right_foot_touch").data[0]
    weight = m.body_subtreemass[m.body("torso").id] * 9.81
    assert abs(touch - weight) / weight < 0.1, (touch, weight)


def test_crouch_within_torque_limit():
    m, d = _load()
    ctrl = np.zeros(m.nu)
    for s in (0, 5):
        # crouch of the bird-type leg: thigh further back (+hip), knee more bent (-knee),
        # foot kept flat: ankle = -(hip + knee)
        ctrl[s + 2], ctrl[s + 3], ctrl[s + 4] = 0.3, -0.6, 0.3
    tilt, h = _upright_after(m, d, ctrl, 5.0)
    assert tilt < 10.0 and h < 0.21, (tilt, h)
    assert np.abs(d.actuator_force).max() < 1.9


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)
