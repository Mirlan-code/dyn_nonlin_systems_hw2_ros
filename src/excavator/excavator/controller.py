import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import JointState


JOINTS = ['turret_joint', 'boom_joint', 'stick_joint', 'bucket_joint']

# Цикл копания: (название, [q1, q2, q3, q4]) в радианах
POSES = [
    ('home',  [0.0,  0.3, 1.2,  1.0]),
    ('reach', [0.0,  1.0, 0.5,  0.2]),
    ('dig',   [0.0,  1.5, 1.2,  0.4]),
    ('scoop', [0.0,  1.2, 1.5,  1.4]),
    ('lift',  [0.0,  0.3, 1.4,  1.4]),
    ('swing', [1.57, 0.3, 1.4,  1.4]),
    ('dump',  [1.57, 0.5, 0.9, -0.8]),
]
SEGMENT_TIME = 2.0


class Controller(Node):

    def __init__(self):
        super().__init__('controller')
        self.pub = self.create_publisher(JointState, 'joint_states', 10)
        self.timer = self.create_timer(1.0 / 30, self.tick)
        self.start = self.now()
        self.segment = 0

    def now(self):
        return self.get_clock().now().nanoseconds * 1e-9

    def tick(self):
        t = self.now() - self.start
        cur_segment = int(t // SEGMENT_TIME) % len(POSES)
        time_diff = (t % SEGMENT_TIME) / SEGMENT_TIME

        name_a, qa = POSES[cur_segment]
        name_b, qb = POSES[(cur_segment + 1) % len(POSES)]
        q = []
        for j in range(len(JOINTS)):
            q.append(qa[j] + time_diff * (qb[j] - qa[j]))

        if cur_segment != self.segment:
            self.segment = cur_segment
            self.get_logger().info(f'{name_a} -> {name_b}')

        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = JOINTS
        msg.position = q
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = Controller()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()