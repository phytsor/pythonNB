import os
import ipaddress
import math
import time

import numpy as np
import capnp

from common.utils_py import *

rc = RheaCaller()


class World(object):
    def __init__(self, rhea_ws_root) -> None:
        self.ev_weight = 0.0

        capnp.add_import_hook(
            [
                os.path.join(rhea_ws_root, "common", "types"),
                os.path.join(rhea_ws_root, "node", "dev", "mt_weigh_module", "types"),
            ]
        )
        capnp.cleanup_global_schema_parser()
        import node_dev_mt_weigh_module_capnp  # type: ignore

        self.weight_mod = node_dev_mt_weigh_module_capnp

    def mountDevices(self):
        # mount elite robot device
        rc.call(
            "/node/dev/elite_arm/service!node_dev_elite_arm:mount",
            {
                "ipv4": int(ipaddress.IPv4Address("192.168.87.130")),
                "path": "/dev/elite_arm",
            },
            check_path_in_params=True,
            call_delay=1,
        )

        # mount hypersen 6d
        rc.call(
            "/node/dev/hypersen_force6d/service!node_dev_hypersen_force6d:mount",
            {
                "ipv4": int(ipaddress.IPv4Address("192.168.87.131")),
                "port": 8080,
                "path": "/dev/hypersen",
            },
            check_path_in_params=True,
            call_delay=1,
        )

        # mount mt weight
        rc.call(
            "/node/dev/mt_weigh_module/service!node_dev_mt_weigh_module:mount",
            {"com": "COM3", "path": "/dev/weight"},
            check_path_in_params=True,
            call_delay=1,
        )

        # mount hk cam h device
        rc.call(
            "/node/dev/hk_cam/service!node_dev_hk_cam:mount",
            {
                "cam": {"ipv4": int(ipaddress.IPv4Address("10.254.62.169"))},
                "path": "/dev/hk-hcam",
            },
            check_path_in_params=True,
            call_delay=1,
        )

        # mount hk cam v device
        rc.call(
            "/node/dev/hk_cam/service!node_dev_hk_cam:mount",
            {
                "cam": {"ipv4": int(ipaddress.IPv4Address("169.254.186.143"))},
                "path": "/dev/hk-vcam",
            },
            check_path_in_params=True,
            call_delay=1,
        )

        # mount img agent
        rc.call(
            "/node/processor/img_agent/service!node_processor_img_agent:mount",
            {
                "cameraType": "hkCam",
                "path": "/processor/v_cam_recorder",
                "streams": ["/dev/hk-vcam/stream"],
            },
            check_path_in_params=True,
            call_delay=1,
        )

        rc.call(
            "/node/processor/img_agent/service!node_processor_img_agent:mount",
            {
                "cameraType": "hkCam",
                "path": "/processor/h_cam_recorder",
                "streams": ["/dev/hk-hcam/stream"],
            },
            check_path_in_params=True,
            call_delay=1,
        )

    def startGrab(self):
        rc.call(
            "/dev/hk-hcam!node_dev_hk_cam:startGrab", check_topic="/dev/hk-hcam/stream"
        )

        rc.call(
            "/dev/hk-vcam!node_dev_hk_cam:startGrab", check_topic="/dev/hk-vcam/stream"
        )

        rc.call(
            "/dev/hypersen!node_dev_hypersen_force6d:startGrab",
            check_topic="/dev/hypersen/stream",
        )

        rc.call("/dev/weight!node_dev_mt_weigh_module:stopGrab", call_delay=1)
        rc.call("/dev/weight!node_dev_mt_weigh_module:setTare", call_delay=1)
        rc.call("/dev/weight!node_dev_mt_weigh_module:startGrab", call_delay=1)

    def getPose(self):
        ret = rc.call(
            "/dev/elite_arm!node_dev_elite_arm:getRobotPose",
        )

        return Pose.fromCommon(ret.pose)

    def wait(func):
        def wrapper(self, *args, **kwargs):
            func(self, *args, **kwargs)
            while True:
                ret = rc.call(
                    "/dev/elite_arm!node_dev_elite_arm:getRobotState",
                )

                if ret.state != "running":
                    break
                time.sleep(0.01)

        return wrapper

    def getJoints(self, degrees=False):
        ret = rc.call(
            "/dev/elite_arm!node_dev_elite_arm:getRobotJoints",
        )
        if degrees:
            degs = []
            for a in ret.degrees:
                degs.append(round(a, 3))
        else:
            degs = np.radians(ret.degrees)
        return degs

    @wait
    def moveJoints(self, radians, speed=50, acc=20, dec=20):
        rc.call(
            "/dev/elite_arm!node_dev_elite_arm:jointMove",
            {
                "degrees": np.degrees(radians).tolist(),
                "speed": speed,
                "acc": acc,
                "dec": dec,
            },
        )

    @wait
    def movePose(self, pose_or_p6, line=False, speed=10):
        err = None
        if isinstance(pose_or_p6, Pose):
            pose = pose_or_p6
        else:
            pose = Pose.fromP6Vec(pose_or_p6)

        ret = rc.call(
            "/dev/elite_arm!node_dev_elite_arm:inverseKinematic",
            {"pose": pose.getCommonParams()},
            call_delay=0.5,
        )

        degrees = ret.degrees
        print(degrees)

        while err is None or err.sub_code == 32693:
            try:
                if line:
                    rc.call(
                        "/dev/elite_arm!node_dev_elite_arm:lineMove",
                        {
                            "degrees": list(degrees),
                            "speed": speed,
                        },
                    )
                else:
                    rc.call(
                        "/dev/elite_arm!node_dev_elite_arm:lineMove",
                        {
                            "degrees": list(degrees),
                            "speed": speed,
                        },
                    )

                break
            except MethodException as e:
                err = e
                time.sleep(0.5)

    @wait
    def addPathPointsRadian(self, radians, speed=10, line=1, smooth=7, acc=2, dec=2):
        err = None
        degrees = []
        for rad in radians:
            degrees.append(rad / np.pi * 180)

        while err is None or err.sub_code == 32693:
            try:
                rc.call(
                    "/dev/elite_arm!node_dev_elite_arm:addPathPoint",
                    {
                        "degrees": list(degrees),
                        "moveType": line,
                        "speed": speed,
                        "smooth": smooth,
                        "acc": acc,
                        "dec": dec,
                    },
                )

                """ c = self.elt1_dev_client.caller("node_dev_elite_arm:addPathPoint")
                c.param.degrees = list(degrees)
                c.param.moveType = line
                c.param.speed = speed
                c.param.smooth = 1
                c.param.acc = 100
                c.param.dec = 100
                c.call() """
                break
            except MethodException as e:
                err = e
                time.sleep(0.5)

    def getDegrees(self, pose_or_p6, radians=False):
        if isinstance(pose_or_p6, Pose):
            pose = pose_or_p6
        else:
            pose = Pose.fromP6Vec(pose_or_p6)

        ret = rc.call(
            "/dev/elite_arm!node_dev_elite_arm:inverseKinematic",
            {"pose": pose.getCommonParams()},
            call_delay=0.5,
        )

        """ c = self.elt1_dev_client.caller("node_dev_elite_arm:inverseKinematic")
        pose.fillCommon(c.param, "pose")
        c.call() """
        degrees = list(ret.degrees)
        rad = []

        if radians:
            for p in degrees:
                rad.append(p / 180 * np.pi)
            return rad

        return degrees

    def getPoseFromDeg(self, degrees):
        err = None

        while err is None or err.sub_code == 32693:
            try:
                ret = rc.call(
                    "/dev/elite_arm!node_dev_elite_arm:positiveKinematic",
                    {"degrees": degrees},
                )

                """ c = self.elt1_dev_client.caller("node_dev_elite_arm:positiveKinematic")
                c.param.degrees = degrees
                c.call() """
                pose = Pose.fromCommon(ret.pose)
                break
            except MethodException as e:
                err = e
                time.sleep(0.5)

        return pose

    @wait
    def addPathPoint(self, pose_or_p6, speed=20):
        err = None
        if isinstance(pose_or_p6, Pose):
            pose = pose_or_p6
        else:
            pose = Pose.fromP6Vec(pose_or_p6)

        ret = rc.call(
            "/dev/elite_arm!node_dev_elite_arm:inverseKinematic",
            {"pose": pose.getCommonParams()},
            call_delay=0.5,
        )

        """ c = self.elt1_dev_client.caller("node_dev_elite_arm:inverseKinematic")
        pose.fillCommon(c.param, "pose")
        c.call() """
        degrees = ret.degrees

        while err is None or err.sub_code == 32693:
            try:
                rc.call(
                    "/dev/elite_arm!node_dev_elite_arm:addPathPoint",
                    {
                        "degrees": list(degrees),
                        "speed": speed,
                        "smooth": 7,
                        "acc": 50,
                        "dec": 50,
                    },
                )

                """ c = self.elt1_dev_client.caller("node_dev_elite_arm:addPathPoint")
                c.param.degrees = list(degrees)
                c.param.speed = speed
                c.param.smooth = 7
                c.param.acc = 50
                c.param.dec = 50
                c.call() """
                break
            except MethodException as e:
                err = e
                time.sleep(0.5)

    @wait
    def pathMove(self):
        err = None

        while err is None or err.sub_code == 32693:
            try:
                rc.call(
                    "/dev/elite_arm!node_dev_elite_arm:pathMove",
                )

                """ c = self.elt1_dev_client.caller("node_dev_elite_arm:pathMove")
                c.call() """
                break
            except MethodException as e:
                err = e
                time.sleep(0.5)

    @wait
    def clearPathPoints(self):
        rc.call("/dev/elite_arm!node_dev_elite_arm:clearPathPoint", call_delay=1)
        """ c = self.elt1_dev_client.caller("node_dev_elite_arm:clearPathPoint")
        c.call() """

    @wait
    def movePoseDelta(self, x=0, y=0, z=0, rx=0, ry=0, rz=0, line=False, tool=None):
        cur_pose = self.getPose()

        if tool is None:
            """tar_pose = Pose.fromP6Vec(
            cur_pose.toP6() + np.array([x, y, z, rx, ry, rz]))"""
            # print(Pose.fromP6(x, y, z, rx, ry, rz))
            # tar_pose = Pose(Pose.fromP6(x, y, z, rx, ry, rz).homo @ cur_pose.homo)
            tar_pose = Pose(cur_pose.homo @ Pose.fromP6Vec([x, y, z, rx, ry, rz]).homo)
        else:
            tool_mat = np.array(
                [
                    [1.0, 0.0, 0.0, tool[0]],
                    [0.0, 1.0, 0.0, tool[1]],
                    [0.0, 0.0, 1.0, tool[2]],
                    [
                        0.0,
                        0.0,
                        0.0,
                        1.0,
                    ],
                ]
            )

            # cur_pose.homo @ tool_mat = tool_global
            # cur_pose.homo' = tool_global' @ tool_mat.I

            tool_global2 = (
                cur_pose.homo @ tool_mat @ Pose.fromP6Vec([x, y, z, rx, ry, rz]).homo
            )
            tar_pose = Pose(tool_global2 @ np.linalg.inv(tool_mat))
            # tar_pose = Pose(getTfromPose([x,y,z,rx,ry,rz]) @ tool_mat @ cur_pose.homo)

        err = None

        ret = rc.call(
            "/dev/elite_arm!node_dev_elite_arm:inverseKinematic",
            {"pose": tar_pose.getCommonParams()},
            call_delay=0.5,
        )

        """ c = self.elt1_dev_client.caller("node_dev_elite_arm:inverseKinematic")
        tar_pose.fillCommon(c.param, "pose")
        c.call() """
        degrees = ret.degrees

        rc.call(
            "/dev/elite_arm!node_dev_elite_arm:clearPathPoint",
        )
        """ c = self.elt1_dev_client.caller("node_dev_elite_arm:clearPathPoint")
        c.call() """

        while err is None or err.sub_code == 32693:
            try:
                rc.call(
                    "/dev/elite_arm!node_dev_elite_arm:addPathPoint",
                    {
                        "degrees": list(degrees),
                        "speed": 50,
                    },
                )

                """ c = self.elt1_dev_client.caller("node_dev_elite_arm:addPathPoint")
                c.param.degrees = list(degrees)
                c.param.speed = 50
                c.call() """
                break
            except MethodException as e:
                print("####", e)
                err = e
                time.sleep(0.5)

        while err is None or err.sub_code == 32693:
            try:
                rc.call(
                    "/dev/elite_arm!node_dev_elite_arm:pathMove",
                )

                """ c = self.elt1_dev_client.caller("node_dev_elite_arm:pathMove")
                c.call() """
                break
            except MethodException as e:
                print("####", e)
                err = e
                time.sleep(0.5)

    def vStartRecord(self, path, size, timeout=6000):
        rc.call(
            "/processor/v_cam_recorder!node_processor_img_agent:startRecord",
            {
                "format": "lmdb",
                "mode": "trigger",
                "path": path,
                "size": size,
                "timeout": timeout,
            },
        )

        """ c = self.v_cam_recorder_client.caller("node_processor_img_agent:startRecord")
        c.param.format = self.img_agent_mod.RecordFormat.lmdb
        c.param.mode = self.img_agent_mod.RecordMode.trigger
        c.param.path = path
        c.param.size = size
        c.param.timeout = timeout
        c.call() """

    def vStopRecord(self):
        rc.call(
            "/processor/v_cam_recorder!node_processor_img_agent:stopRecord",
        )

        """ c = self.v_cam_recorder_client.caller("node_processor_img_agent:stopRecord")
        c.call()"""

    def vTrigger(self, trigger_id, count=5):
        rc.call(
            "/processor/v_cam_recorder!node_processor_img_agent:trigger",
            {
                "count": count,
                "triggerId": trigger_id,
            },
        )

        """ c = self.v_cam_recorder_client.caller("node_processor_img_agent:trigger")
        c.param.count = count
        c.param.triggerId = trigger_id
        c.call() """

    def hStartRecord(self, path, size, timeout=600):
        rc.call(
            "/processor/h_cam_recorder!node_processor_img_agent:startRecord",
            {
                "format": "lmdb",
                "mode": "trigger",
                "path": path,
                "size": size,
                "timeout": timeout,
            },
        )

        """ c = self.h_cam_recorder_client.caller("node_processor_img_agent:startRecord")
        c.param.format = self.img_agent_mod.RecordFormat.lmdb
        c.param.mode = self.img_agent_mod.RecordMode.trigger
        c.param.path = path
        c.param.size = size
        c.param.timeout = timeout
        c.call() """

    def hStopRecord(self):
        rc.call(
            "/processor/h_cam_recorder!node_processor_img_agent:stopRecord",
        )

        """ c = self.h_cam_recorder_client.caller("node_processor_img_agent:stopRecord")
        c.call() """

    def hTrigger(self, trigger_id, count=5):
        rc.call(
            "/processor/h_cam_recorder!node_processor_img_agent:trigger",
            {
                "count": count,
                "triggerId": trigger_id,
            },
        )

        """ c = self.h_cam_recorder_client.caller("node_processor_img_agent:trigger")
        c.param.count = count
        c.param.triggerId = trigger_id
        c.call() """

    def rad2deg(self, pose):
        degrees = []
        for i in range(0, len(pose)):
            degrees.append(pose[i] / np.pi * 180)
        return degrees

    def listenWeight(self):
        self.weight_sub = BlobSubscriber(
            "/dev/weight/stream", "node_dev_mt_weigh_module:WeightData"
        )
        self.weight_sub.set_callback(self.weightCallback)

    def weightCallback(self, topic_name, msg, time):
        with self.weight_mod.WeightData.from_bytes(msg) as weightMsg:
            self.crt_weight = weightMsg
