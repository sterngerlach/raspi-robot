# coding: utf-8
# servo_motor_node.py

from command_receiver_node import CommandReceiverNode, UnknownCommandException

class ServoMotorNode(CommandReceiverNode):
    """
    サーボモータを操作するクラス
    """

    def __init__(self, process_manager, msg_queue, servo_id, servo_motor):
        """コンストラクタ"""
        super().__init__(process_manager, msg_queue)
        
        # サーボモータのID
        self.servo_id = servo_id
        # サーボモータのインスタンス
        self.servo_motor = servo_motor

    def initialize_state_dict(self):
        """ノードの状態を格納するディクショナリを初期化"""
        super().initialize_state_dict()

        # サーボモータの角度をディクショナリに格納
        self.state_dict["angle"] = 0

    def process_command(self):
        """サーボモータへの命令を処理"""
        
        try:
            while True:
                # サーボモータへの命令をキューから取り出し
                cmd = self.command_queue.get()
                print("ServoMotorNode::process_command(): command received: {0}"
                      .format(cmd))
                
                # 適切な命令でない場合は例外をスロー
                if "angle" not in cmd and "value" not in cmd:
                    raise UnknownCommandException(
                        "ServoMotorNode::process_command(): unknown command: {0}"
                        .format(cmd))

                # 命令の実行開始をアプリケーションに伝達
                self.send_message("servo" + str(self.servo_id), { "command": cmd, "state": "start" })

                if "angle" in cmd:
                    # サーボモータの角度を指定
                    self.servo_motor.set_angle(cmd["angle"])
                    # 最後に指定した角度を更新
                    self.state_dict["angle"] = cmd["angle"]
                elif "value" in cmd:
                    # サーボモータのGPIO端子に値を書き込み
                    self.servo_motor.write(cmd["value"])
                
                # 命令の実行終了をアプリケーションに伝達
                self.send_message("servo" + str(self.servo_id), { "command": cmd, "state": "done" })

                # サーボモータへの命令が完了
                self.command_queue.task_done()

        except KeyboardInterrupt:
            # プロセスが割り込まれた場合
            print("ServoMotorNode::process_command(): KeyboardInterrupt occurred")

