"""Fusion export (biped_v0) -> MJCF converter.

Input  : models/biped_v0/cad_export/biped_v0_v4_properties.json  (CAD world frame, mm / g / g*mm^2)
         models/biped_v0/cad_export/meshes_cad/*.stl              (CAD world frame, mm, as-built pose)
Output : models/biped_v0/biped_v0.xml, models/biped_v0/meshes/*.stl

Frame / unit conversion (see models/biped_v0/README.md):
    robot +x (forward) = CAD +Z
    robot +y (left)    = CAD +X
    robot +z (up)      = CAD +Y
    mm -> m, g -> kg, g*mm^2 -> kg*m^2

Values marked PROVISIONAL are not decided in docs/reference/decision_pending.md and are
kept in one place (PROVISIONAL dict) so they can be replaced after identification.

Usage:
    uv run --extra sim python tools/cad_to_mjcf.py
"""

from __future__ import annotations

import json
import struct
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "models" / "biped_v0"
CAD_DIR = MODEL_DIR / "cad_export"
PROPS = CAD_DIR / "biped_v0_v4_properties.json"

# CAD -> robot rotation (proper rotation, det = +1)
R_CAD2ROBOT = np.array([[0.0, 0.0, 1.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
MM = 1e-3
G = 1e-3
GMM2 = 1e-9

# Joint ordering = docs/reference/joint_definition.md (index 0..9)
JOINTS = [
    "left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee_pitch", "left_ankle_pitch",
    "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee_pitch", "right_ankle_pitch",
]
# Positive joint axis in the robot frame (right-hand rule): yaw +z, roll +x, pitch +y.
AXIS = {"hip_yaw": (0, 0, 1), "hip_roll": (1, 0, 0), "hip_pitch": (0, 1, 0),
        "knee_pitch": (0, 1, 0), "ankle_pitch": (0, 1, 0)}
# Child body name in MJCF for each joint suffix
CHILD_BODY = {"hip_yaw": "hip_yaw_link", "hip_roll": "hip_roll_link", "hip_pitch": "thigh_link",
              "knee_pitch": "shin_link", "ankle_pitch": "foot_link"}

PROVISIONAL = {
    # DP-010: joint range [rad] around the CAD as-built pose (q = 0). Not interference-checked.
    # knee: q = +0.698 rad makes the leg straight (thigh / shin collinear) -> upper limit kept below it.
    "range": {"hip_yaw": (-0.5, 0.5), "hip_roll": (-0.4, 0.4), "hip_pitch": (-1.0, 1.0),
              "knee_pitch": (-1.3, 0.6), "ankle_pitch": (-1.0, 1.0)},
    # DP-012 / Phase 3 actuator identification: STS3215 C001 (1:345) stall 19.5 kgf*cm @7.4 V ~= 1.91 N*m
    "kp": 8.0,            # N*m/rad
    "kv": 0.2,            # N*m*s/rad
    "forcerange": 1.9,    # N*m
    "armature": 0.005,    # kg*m^2
    "damping": 0.05,      # N*m*s/rad
    "frictionloss": 0.03, # N*m
    "foot_friction": 0.8,
}


def read_stl(path: Path) -> np.ndarray:
    data = path.read_bytes()
    n = struct.unpack("<I", data[80:84])[0]
    rec = np.frombuffer(data, dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")], count=n, offset=84)
    return rec["v"].astype(float)  # (n, 3, 3)


def write_stl(path: Path, tri: np.ndarray, header: str) -> None:
    nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    ln = np.linalg.norm(nrm, axis=1, keepdims=True)
    nrm = np.divide(nrm, ln, out=np.zeros_like(nrm), where=ln > 0)
    rec = np.zeros(len(tri), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"], rec["v"] = nrm, tri
    with path.open("wb") as f:
        f.write(header.encode()[:80].ljust(80, b" "))
        f.write(struct.pack("<I", len(tri)))
        f.write(rec.tobytes())


def to_robot(p_mm) -> np.ndarray:
    return R_CAD2ROBOT @ np.asarray(p_mm, float) * MM


def inertia_com_cad(link: dict) -> np.ndarray:
    """Inertia tensor about the CoM in the CAD frame [g*mm^2], from principal values/axes.
    Cross-checked against Fusion's XYZ moments about the world origin (parallel-axis theorem)."""
    p = np.array(link["I_principal_gmm2"])
    A = np.array(link["principal_axes"])
    I = sum(p[i] * np.outer(A[i], A[i]) for i in range(3))
    m = link["mass_g"]
    c = np.array(link["com_mm"])
    xx, yy, zz, xy, yz, xz = link["I_xyz_origin_gmm2"]
    I_origin = np.array([[xx, xy, xz], [xy, yy, yz], [xz, yz, zz]])
    I_pa = I + m * (c @ c * np.eye(3) - np.outer(c, c))
    err = np.abs(I_pa - I_origin).max() / np.abs(I_origin).max()
    assert err < 1e-3, f"inertia cross-check failed ({err:.2e})"
    return I


def obb(verts: np.ndarray, axis_x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Box with its local x along axis_x (in the xz plane) and local y = robot y."""
    ex = axis_x / np.linalg.norm(axis_x)
    ey = np.array([0.0, 1.0, 0.0])
    ez = np.cross(ex, ey)
    R = np.column_stack([ex, ey, ez])
    loc = verts @ R
    lo, hi = loc.min(0), loc.max(0)
    center = R @ ((lo + hi) / 2)
    half = (hi - lo) / 2
    # rotation matrix -> quaternion (w, x, y, z)
    w = np.sqrt(max(0.0, 1 + R[0, 0] + R[1, 1] + R[2, 2])) / 2
    q = np.array([w, (R[2, 1] - R[1, 2]) / (4 * w), (R[0, 2] - R[2, 0]) / (4 * w), (R[1, 0] - R[0, 1]) / (4 * w)])
    return center, half, q


def f(v, n=6) -> str:
    return " ".join(f"{x:.{n}g}" if abs(x) > 1e-12 else "0" for x in np.atleast_1d(v))


def main() -> None:
    props = json.loads(PROPS.read_text())
    links, joints = props["links"], props["joints"]
    side_suffix = {"left": "_L", "right": "_R"}  # Fusion component suffix by robot side (renamed in v4)
    cad_link = {"hip_yaw": "yaw_to_roll_body", "hip_roll": "roll_to_pitch_body", "hip_pitch": "pitch_to_knee_body",
                "knee_pitch": "ankle", "ankle_pitch": "foot"}

    mesh_out = MODEL_DIR / "meshes"
    mesh_out.mkdir(exist_ok=True)

    def link_block(cad_name: str, body: str, origin: np.ndarray, indent: str, collision: str) -> list[str]:
        L = links[cad_name]
        m = L["mass_g"] * G
        com = to_robot(L["com_mm"]) - origin
        I = R_CAD2ROBOT @ inertia_com_cad(L) @ R_CAD2ROBOT.T * GMM2
        tri = (np.einsum("ij,nkj->nki", R_CAD2ROBOT, read_stl(CAD_DIR / "meshes_cad" / f"{cad_name}.stl")) * MM) - origin
        write_stl(mesh_out / f"{body}.stl", tri, f"biped_v0 v4 {body} body frame [m]")
        out = [
            f'{indent}<inertial pos="{f(com)}" mass="{m:.6g}" '
            f'fullinertia="{f([I[0,0], I[1,1], I[2,2], I[0,1], I[0,2], I[1,2]])}"/>',
            f'{indent}<geom class="visual" mesh="{body}"/>',
        ]
        if collision:
            out.append(indent + collision)
        return out, tri.reshape(-1, 3)

    lines: list[str] = []
    meshes: list[str] = []
    torso_origin = np.zeros(3)  # torso frame = CAD origin (DP-019 provisional)
    blk, torso_v = link_block("main_body", "torso", torso_origin, "      ", "")
    lo, hi = torso_v.min(0), torso_v.max(0)
    torso_col = f'<geom name="torso_collision" class="collision" type="box" pos="{f((lo+hi)/2)}" size="{f((hi-lo)/2)}"/>'
    meshes.append("torso")
    lines += ['    <body name="torso" pos="0 0 0" childclass="biped_v0">', '      <freejoint name="floating_base"/>',
              '      <site name="imu" pos="0 0 0" size="0.005"/>'] + blk + [f"      {torso_col}"]

    foot_bottom = []
    for side in ("left", "right"):
        parent_origin = torso_origin
        depth = 3
        opened = 0
        jnames = [j for j in JOINTS if j.startswith(side)]
        for k, jn in enumerate(jnames):
            suffix = jn[len(side) + 1:]
            J = joints[jn]
            origin = to_robot(J["origin_mm"])
            cad_name = cad_link[suffix] + side_suffix[side]
            assert J["child"] == cad_name, (jn, J["child"], cad_name)
            body = f"{side}_{CHILD_BODY[suffix]}"
            ind = "  " * depth
            lines.append(f'{ind}<body name="{body}" pos="{f(origin - parent_origin)}">')
            lo_r, hi_r = PROVISIONAL["range"][suffix]
            lines.append(f'{ind}  <joint name="{jn}" class="sts3215" axis="{f(AXIS[suffix])}" range="{lo_r} {hi_r}"/>')
            # cad axis expressed in robot frame, for the sign table in README
            J["axis_robot_from_cad"] = (R_CAD2ROBOT @ np.array(J["axis"])).round(6).tolist()
            # collision geometry
            col = ""
            tri_v = (np.einsum("ij,nkj->nki", R_CAD2ROBOT, read_stl(CAD_DIR / "meshes_cad" / f"{cad_name}.stl")) * MM - origin).reshape(-1, 3)
            if suffix == "hip_yaw":
                lo, hi = tri_v.min(0), tri_v.max(0)
                col = f'<geom name="{body}_collision" class="collision" type="box" pos="{f((lo+hi)/2)}" size="{f((hi-lo)/2)}"/>'
            elif suffix in ("hip_pitch", "knee_pitch"):
                nxt = to_robot(joints[jnames[k + 1]]["origin_mm"]) - origin
                c, h, q = obb(tri_v, np.array([nxt[0], 0.0, nxt[2]]))
                col = f'<geom name="{body}_collision" class="collision" type="box" pos="{f(c)}" quat="{f(q)}" size="{f(h)}"/>'
            elif suffix == "ankle_pitch":
                lo, hi = tri_v.min(0), tri_v.max(0)
                # sole plate only (5 mm); the ankle bracket above it is left without collision
                sole_c = np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2] + 0.0025])
                col = (f'<geom name="{body}_collision" class="foot" type="box" pos="{f(sole_c)}" '
                       f'size="{f([(hi[0]-lo[0])/2, (hi[1]-lo[1])/2, 0.0025])}"/>')
                sole = np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2] + 0.002])
                lines.append(f'{ind}  <site name="{side}_foot_sole" type="box" pos="{f(sole)}" '
                             f'size="{f([(hi[0]-lo[0])/2 + 0.002, (hi[1]-lo[1])/2 + 0.002, 0.004])}" rgba="0 1 0 0.2"/>')
                foot_bottom.append((origin + lo)[2])
            blk, _ = link_block(cad_name, body, origin, ind + "  ", col)
            lines += blk
            meshes.append(body)
            parent_origin = origin
            depth += 1
            opened += 1
        for d in range(opened):
            depth -= 1
            lines.append("  " * depth + "</body>")
    lines.append("    </body>")

    base_height = -min(foot_bottom) + 1e-4
    P = PROVISIONAL
    xml = f"""<!--
  biped_v0 (Fusion "biped_v0" v{props['version']}) -> MJCF. GENERATED by tools/cad_to_mjcf.py; do not edit by hand.
  Frame: +x forward, +y left, +z up [m, kg, rad]. q = 0 is the CAD as-built pose (hip pitch 20 deg, knee 40 deg bent).
  PROVISIONAL values (joint range, actuator, friction, torso frame) are listed in models/biped_v0/README.md.
-->
<mujoco model="biped_v0">
  <compiler angle="radian" meshdir="meshes" autolimits="true"/>
  <option timestep="0.002" integrator="implicitfast"/>

  <default>
    <default class="biped_v0">
      <joint damping="{P['damping']}" armature="{P['armature']}" frictionloss="{P['frictionloss']}"/>
      <default class="sts3215">
        <joint type="hinge"/>
        <position kp="{P['kp']}" kv="{P['kv']}" forcerange="-{P['forcerange']} {P['forcerange']}"/>
      </default>
      <default class="visual">
        <geom type="mesh" contype="0" conaffinity="0" group="2" density="0" rgba="0.25 0.25 0.28 1"/>
      </default>
      <default class="collision">
        <geom group="3" contype="1" conaffinity="1" density="0" rgba="0.8 0.3 0.3 0.4"/>
        <default class="foot">
          <geom condim="3" friction="{P['foot_friction']} 0.02 0.01" priority="1"/>
        </default>
      </default>
    </default>
  </default>

  <asset>
{chr(10).join(f'    <mesh name="{m}" file="{m}.stl"/>' for m in meshes)}
  </asset>

  <worldbody>
{chr(10).join(lines)}
  </worldbody>

  <contact>
{{EXCLUDES}}
  </contact>

  <actuator>
{chr(10).join(f'    <position name="{j}" class="sts3215" joint="{j}" ctrlrange="{P["range"][j.split("_", 1)[1]][0]} {P["range"][j.split("_", 1)[1]][1]}"/>' for j in JOINTS)}
  </actuator>

  <sensor>
    <gyro name="imu_gyro" site="imu"/>
    <accelerometer name="imu_accel" site="imu"/>
    <framequat name="imu_quat" objtype="site" objname="imu"/>
    <velocimeter name="imu_linvel" site="imu"/>
    <touch name="left_foot_touch" site="left_foot_sole"/>
    <touch name="right_foot_touch" site="right_foot_sole"/>
  </sensor>

  <keyframe>
    <key name="home" qpos="0 0 {base_height:.5f} 1 0 0 0 {' '.join(['0'] * 10)}" ctrl="{' '.join(['0'] * 10)}"/>
  </keyframe>
</mujoco>
"""
    # self-collision exclusions: same-leg, non parent/child pairs that overlap at q = 0
    import mujoco  # noqa: PLC0415

    tmp = MODEL_DIR / "biped_v0.xml"
    tmp.write_text(xml.replace("{EXCLUDES}", ""))
    model = mujoco.MjModel.from_xml_path(str(tmp))
    data = mujoco.MjData(model)
    mujoco.mj_resetDataKeyframe(model, data, 0)
    data.qpos[2] += 0.05  # lift: floor contacts are not self-collisions
    mujoco.mj_forward(model, data)
    pairs = set()
    for i in range(data.ncon):
        c = data.contact[i]
        b1, b2 = model.geom_bodyid[c.geom1], model.geom_bodyid[c.geom2]
        n1, n2 = model.body(b1).name, model.body(b2).name
        pairs.add(tuple(sorted((n1, n2))))
    excl = "\n".join(f'    <exclude body1="{a}" body2="{b}"/>' for a, b in sorted(pairs))
    tmp.write_text(xml.replace("{EXCLUDES}", excl))
    (CAD_DIR / "joint_axis_mapping.json").write_text(json.dumps(
        {j: {"axis_robot": AXIS[j.split("_", 1)[1]], "cad_axis_in_robot_frame": joints[j]["axis_robot_from_cad"]}
         for j in JOINTS}, indent=2))
    print("wrote", tmp, "| home base height", round(base_height, 5), "| self-collision excludes:", sorted(pairs))


if __name__ == "__main__":
    main()
