
# robot\_libの説明書き

## 基本的なクラス群

### `Node`クラス

各ノードを表す基底クラス。

- `process_manager`

    プロセス間で共有するオブジェクトを作成するために利用されるマネージャオブジェクト(`multiprocessing.managers.SyncManager`クラスのインスタンス)です。`multiprocessing.Manager()`メソッドにより作成されます。

- `state_dict`

    ノードの状態を格納するためのディクショナリで、各ノードとアプリケーションの間で共有されています。`dict`オブジェクトのプロキシで、`multiprocessing.managers.SyncManager.dict()`メソッドにより作成されます。各ノードでは`state_dict`に自由な項目を追加することができます(アプリケーションがその項目を参照します)。

- `msg_queue`

    各ノードからアプリケーションへのメッセージを格納するキューで、全ノード間で共有されています。`queue.Queue`オブジェクトのプロキシで、`multiprocessing.managers.SyncManager.Queue()`メソッドにより作成されます。`send_message()`メソッドによってノードからアプリケーションに向けてメッセージを送ることができます。

- `__init__()`

    ノードを初期化します。`initialize_state_dict()`メソッドが内部で呼び出されます。

- `initialize_state_dict()`

    ノードの状態を格納するディクショナリ`state_dict`を初期化します。各ノードは必要に応じてこのメソッドをオーバーライドすることができます。

- `run()`

    ノードの実行を開始します(抽象メソッドであるため呼び出すことはできません)。

- `send_message(sender_name, msg)`

    ノードからアプリケーションに向けてメッセージを送信します。引数`sender_name`はメッセージの送り主の名前(ID)、引数`msg`はメッセージ(文字列やディクショナリ型)です。メッセージは次のように辞書型に変換された上で、キュー`msg_queue`に追加されます。

    ```python
    { "sender": sender_name, "content": msg }
    ```

### `DataSenderNode`クラス

データを読み取ってアプリケーションに送信するノードを表す基底クラス(`Node`クラスを継承)。例えば超音波センサのノード(`Srf02Node`クラス)は、センサからの値を読み取ってアプリケーション側に伝える役割を持ち、アプリケーションからの指示に従って動作を変更することはないため、このクラスを継承します。サーボモータのノードでは、アプリケーションからモータに命令を送信する必要があるため、`CommandReceiverNode`クラスを継承する必要があります。

- `process_handler`

    `multiprocessing.Process`クラスのオブジェクトで、`update()`メソッドを別プロセスで実行するために使用されます。`update()`メソッドを実行するプロセスはデーモンプロセスであるため、親プロセス(アプリケーションのプロセス)が終了すると自動的に終了します。

- `__init__`

    ノードを初期化します。`Node`クラスのコンストラクタが最初に呼び出され、次に`initialize_process_handler()`メソッドが呼び出されます。

- `initialize_process_handler()`

    `process_handler`を初期化するためにコンストラクタ内で呼び出されます。アプリケーション側で勝手に呼び出してはいけません。

- `update()`

    入力を処理して、`Node.send_message()`メソッドによりアプリケーションにメッセージを送信したり、`Node.state_dict`を必要に応じて更新したりするためのメソッドです。`DataSenderNode`クラスを継承したクラスではこのメソッドをオーバーライドします。アプリケーション側で勝手に呼び出してはいけません。

- `run()`

    `update()`メソッドを実行する子プロセスを開始するために、`NodeManager`クラスから呼び出されます。アプリケーション側で勝手に呼び出してはいけません。

### `CommandReceiverNode`クラス

アプリケーションから命令を受信して実行するノードを表す基底クラス(`Node`クラスを継承)。但し`Node`クラスを継承しているので、ノードからアプリケーションに対してメッセージを送信することも可能です。モータのノード(`MotorNode`)、サーボモータのノード(`ServoMotorNode`)、音声合成のノード(`OpenJTalkNode`)などがこのクラスを継承しています。

- `command_queue`

    アプリケーションからノードへの命令を保持するキューで、各ノードとアプリケーションの間で共有されています。`queue.Queue`オブジェクトのプロキシで、`multiprocessing.managers.SyncManager.Queue()`メソッドにより作成されます。アプリケーションは、`NodeManager.send_command()`メソッドを呼び出すことで、各ノードに対して命令を送信できます。

- `process_handler`

    `multiprocessing.Process`クラスのオブジェクトで、`process_command`メソッドを別プロセスで実行するために使用されます。`process_command`メソッドを実行するプロセスはデーモンプロセスであるため、親プロセス(アプリケーションや`NodeManager`クラスを実行しているプロセス)が終了すると自動的に終了します。

- `__init__`

    ノードを初期化します。`Node`クラスのコンストラクタが最初に呼び出され、`initialize_command_queue()`、`initialize_process_handler()`メソッドが順に呼び出されます。

- `initialize_command_queue()`
    
    アプリケーションからノードへの命令を格納するキュー`command_queue`を初期化します。アプリケーションが勝手に呼び出してはいけません。

- `initialize_process_handler()`

    `process_handler`を初期化するためにコンストラクタ内で呼び出されます。アプリケーションが勝手に呼び出してはいけません。

- `process_command()`
    
    アプリケーションから送信された命令をキュー`command_queue`から取り出して、命令を解釈し実行するためのメソッドです。別プロセスで実行されます。アプリケーション側で勝手に呼び出してはいけません。

- `send_command(cmd)`

    命令をキュー`command_queue`に追加します。アプリケーション側のプロセスでこのメソッドを呼び出します。

- `wait_until_all_command_done()`
    
    キューから全ての命令が取り出されて空になるまで実行をブロックします。アプリケーション側のプロセスでこのメソッドを呼び出します。

- `run()`

    命令を実行する子プロセスを開始するために、`NodeManager`クラスから呼び出されます。アプリケーション側で呼び出す場合があります。

- `terminate()`

    命令を実行する子プロセスを強制終了させるために、アプリケーション側のプロセスで呼び出すことができます。プロセスを強制終了すると、実行途中の命令は中断されます。また、`initialize_state_dict()`メソッドが呼び出されるので、ノードの状態を保持するディクショナリは初期化されます。更に、`initialize_command_queue()`メソッドが呼び出されてキュー`command_queue`が初期化されるため、強制終了時にキュー`command_queue`内に残っていた未実行の命令は全て破棄され、実行されることはありません。`initialize_process_handler()`メソッドの呼び出しによって、再びノードの実行を開始できるようになります(`run()`メソッドの呼び出しが可能になる)。

### `UnknownCommandException`クラス

受信したコマンドが不明である場合に`CommandReceiverNode`クラスを継承したノードが送出する例外です。

### `NodeManager`クラス

全てのノードを管理するためのクラスでアプリケーションが直接利用するものです。

- `__init__(config_dict)`

    コンストラクタ。ロボットの設定を記述したディクショナリ`config_dict`を引数に取ります。`config_dict`は次のようになります(全てのノードを有効化する場合)。`enable`で始まるキーは必ず追加しておく必要があります。モータを使用する場合は、GPIOの端子やSPIチャネルが自動的に初期化されるため、各ノードのクラス内でこれらを初期化する必要はありません。

    **顔検出ノード(`enable_webcam`)とトランプカードの検出ノード(`enable_card`)の両方を有効化することはできません(片方のみを有効化してください)**。

    ```python
    config = {
        "enable_motor": True,       # 左右のモータを有効化
        "enable_servo": True,       # サーボモータを有効化
        "enable_srf02": True,       # 超音波センサを有効化
        "enable_julius": True,      # 音声認識エンジンJuliusのノードを有効化
        "enable_openjtalk": True,   # 音声合成システムOpenJTalkのノードを有効化
        "enable_speechapi": False,  # 音声認識(Google Cloud Speech API)を有効化(非推奨)
        "enable_webcam": True,      # 人の顔を認識するノードを有効化
        "enable_card": False,       # トランプカードを認識するノードを有効化

        "motor": {},                # モータの設定(特に設定内容は無いため空のディクショナリを指定)
        "servo": {},                # サーボモータの設定(特になし)
        "srf02": {                          # 超音波センサの設定
            "distance_threshold": 15,       # 障害物に接近したと判定するための距離の閾値
            "near_obstacle_threshold": 5,   # 測定値を連続で何度下回ったときに障害物の接近と判断するか
            "interval": 0.25,               # 距離の計測を行う間隔(秒)
            "addr_list": [0x70, 0x71]       # 超音波センサのアドレスのリスト
        },
        "julius": {},               # Juliusの設定(特になし)
        "openjtalk": {},            # OpenJTalkの設定(特になし)
        "speechapi": {},            # Google Speech APIの設定(特になし)
        "webcam": {                         # 人の顔を認識するノードの設定
            "camera_id": 0,                 # ウェブカメラのID
            "interval": 1.0,                # 顔検出を行う間隔(秒)
            "frame_width": 640,             # ウェブカメラの横方向の解像度
            "frame_height": 480             # ウェブカメラの縦方向の解像度
        },
        "card": {                           # トランプカードを認識するノードの設定
            "server_host": "192.168.0.123", # トランプカードの認識を行うサーバのホスト名またはIPアドレス
            "camera_id": 0,                 # ウェブカメラのID
            "frame_width": 640,             # ウェブカメラの横方向の解像度
            "frame_height": 480             # ウェブカメラの縦方向の解像度
        }
    }

    node_manager = NodeManager(config)
    ```

- `run_nodes()`

    有効化したノードの実行を開始します。アプリケーションの実行開始時に1度だけ呼び出します。

- `send_command(name, cmd)`

    引数`name`で指定されたノードにコマンド`cmd`を送信します。引数`cmd`はディクショナリ型でなければなりません。また、`name`に指定できるのは、`motor`(左右のモータ)、`servo`(サーボモータ)、`srf02`(超音波センサ)、`julius`(Julius)、`openjtalk`(OpenJTalk)、`speechapi`(Google Cloud Speech API)、`webcam`(ウェブカメラ)のいずれかです(今後追加される可能性が高いです)。

- `get_node(name)`

    引数`name`で指定されたノード(`DataSenderNode`または`CommandReceiverNode`クラスを継承)を取得します。

- `get_node_state(name)`

    引数`name`で指定されたノード(`DataSenderNode`または`CommandReceiverNode`クラスを継承)が保持している状態のディクショナリ(`state_dict`)を取得します。

- `get_msg_queue()`

    各ノードからアプリケーションに向けて送信されるメッセージのキューを取得します。

## 各ノードのクラス

### `MotorNode`クラス

`CommandReceiverNode`クラスを継承しており、アプリケーションからの指示に従って左右のモータを実際に動作させます。

#### 各種変換関数

- `convert_speed_to_steps_per_second(speed)`

    モータの速度を1秒間あたりのステップ数に変換します。モータの速度は後述するコマンドで指定します。

- `convert_steps_per_second_to_speed(steps_per_second)`

    1秒間あたりのステップ数をモータの速度に変換します。

- `convert_speed_to_centimeters_per_second(speed)`

    モータの速度を車輪の回転速度(センチメートル毎秒)に変換します。

- `convert_centimeters_per_second_to_speed(centimeters_per_second)`

    車輪の回転速度(センチメートル毎秒)をモータの速度に変換します。

- `convert_speed_to_revolutions_per_second(speed)`

    モータの速度を1秒間あたりの車輪の回転数に変換します。

- `convert_revolutions_per_second_to_speed(revolutions_per_second)`

    1秒間あたりの車輪の回転数をモータの速度に変換します。

- `calculate_turning_angle_velocity(left_velocity, right_velocity)`

    左右の車輪の回転速度(センチメートル毎秒)からロボットの旋回角速度(ラジアン毎秒)を計算します。

- `calculate_turning_radius(left_velocity, right_velocity)`

    左右の車輪の回転速度(センチメートル毎秒)からロボットの旋回半径(センチメートル)を計算します。

- `calculate_center_velocity(left_velocity, right_velocity)`

    左右の車輪の回転速度(センチメートル毎秒)からロボットの中心速度(センチメートル毎秒)を計算します。

- `calculate_left_velocity(turning_radius, turning_angle_velocity)`
    
    ロボットの旋回半径(センチメートル)とロボットの旋回角速度(ラジアン毎秒)から、左の車輪の回転速度(センチメートル毎秒)を計算します。

- `calculate_right_velocity(turning_radius, turning_angle_velocity)`
    
    ロボットの旋回半径(センチメートル)とロボットの旋回角速度(ラジアン毎秒)から、右の車輪の回転速度(センチメートル毎秒)を計算します。

#### 共有変数の内容

- `state_dict["speed_left"]`
    
    左側のモータの現在の速度を格納します。

- `state_dict["speed_right"]`

    右側のモータの現在の速度を格納します。

#### アプリケーションからノードに送られるメッセージ

アプリケーションからは次のような命令を送信できます。

- set-speedコマンド

    左右両方のモータの速度を設定します。`command`キーには`set-speed`を指定します。`speed_left`キーに左側のモータの速度、`speed_right`キーに右側のモータの速度、`step_left`キーに左側のモータの速度のループ1回あたりの増減分、`step_right`キーに右側のモータの速度のループ1回あたりの増減分、`wait_time`キーにループ1回あたりの待ち時間(秒単位)をそれぞれ指定します。`wait_time`キーに指定する値を小さくすると、また`step_left`と`step_right`に指定する値を大きくすると、モータの速度変化は急峻になります。`step_left`、`step_right`、`wait_time`には正の値を指定してください。`speed_left`と`speed_right`は、正の値を指定すると前進、負の値を指定すると後進を意味します。
    
    ```python
    node_manager.send_command("motor",
        { "command": "set-speed",
          "speed_left": 9000, "speed_right": 3000,
          "step_left": 300, "step_right": 250,
          "wait_time": 0.05 })
    ```

    1回のループでの速度の増減分を`step`で始まるキーに、1回のループの実行後の待ち時間を`wait_time`キーに指定します。分かりやすく説明すると、階段の1段の高さが`step`、階段の幅が`wait_time`ということです。`set-speed`コマンドを実行すると次の`MotorNode::set_speed()`メソッドが呼び出されます。

    ```python
    def set_speed(self, speed_left, speed_right, step_left, step_right, wait_time):
        """2つのモータの速度を設定(速度は階段状に変化)"""

        left_op = 1 if speed_left > self.state_dict["speed_left"] \
                  else -1 if speed_left < self.state_dict["speed_left"] \
                  else 0
        right_op = 1 if speed_right > self.state_dict["speed_right"] \
                   else -1 if speed_right < self.state_dict["speed_right"] \
                   else 0

        while True:
            # モータの速度変更の終了を判定
            left_done = \
                self.state_dict["speed_left"] >= speed_left if left_op == 1 \
                else self.state_dict["speed_left"] <= speed_right if left_op == -1 \
                else True
            right_done = \
                self.state_dict["speed_right"] >= speed_right if right_op == 1 \
                else self.state_dict["speed_right"] <= speed_right if right_op == -1 \
                else True

            if left_done and right_done:
                break
            
            # モータの速度を段階的に変更
            if not left_done:
                self.state_dict["speed_left"] = \
                    min(self.state_dict["speed_left"] + step_left, speed_left) if left_op == 1 \
                    else max(self.state_dict["speed_left"] - step_left, speed_left) if left_op == -1 \
                    else self.state_dict["speed_left"]
                self.motor_left.run(self.state_dict["speed_left"])

            if not right_done:
                self.state_dict["speed_right"] = \
                    min(self.state_dict["speed_right"] + step_right, speed_right) if right_op == 1 \
                    else max(self.state_dict["speed_right"] - step_right, speed_right) if right_op == -1 \
                    else self.state_dict["speed_right"]
                self.motor_right.run(self.state_dict["speed_right"])
            
            time.sleep(wait_time)
    ```


- set-left-speedコマンド

    左側のモータの速度を設定します。`command`キーには`set-left-speed`を指定します。`speed`キーにモータの速度、`step`キーにループ1回あたりの増減分、`wait_time`キーにループ1回あたりの待ち時間をそれぞれ指定します。`step`と`wait_time`には正の値を指定してください。`speed`は正の値を指定すると前進、負の値を指定すると後進を意味します。

    ```python
    node_manager.send_command("motor",
        { "command": "set-left-speed",
          "speed": 9000, "step": 300, "wait_time": 0.06 })
    ```

- set-right-speedコマンド

    右側のモータの速度を設定します。`command`キーには`set-right-speed`を指定します。`speed`キーにモータの速度、`step`キーにループ1回あたりの増減分、`wait_time`キーにループ1回あたりの待ち時間をそれぞれ指定します。`step`と`wait_time`には正の値を指定してください。`speed`は正の値を指定すると前進、負の値を指定すると後進を意味します。

    ```python
    node_manager.send_command("motor",
        { "command": "set-right-speed",
          "speed": 3000, "step": 250, "wait_time": 0.03 })
    ```

- set-speed-immコマンド

    左右両方のモータの速度を設定します。`command`キーには`set-speed-imm`を指定します(immはimmediateの略です)。set-speedのように徐々に速度を変化させていくのではなく、直ちに指定された速度に変更します。`speed_left`キーには左側のモータの速度、`speed_right`には右側のモータの速度を指定します。

    ```python
    node_manager.send_command("motor",
        { "command": "set-speed-imm",
          "speed_left": 9000, "speed_right": 3000 })
    ```

- set-left-speed-immコマンド

    左側のモータの速度を設定します。`command`キーには`set-left-speed-imm`を指定します。set-left-speedのように徐々に速度を変化させていくのではなく、直ちに指定された速度に変更します。`speed`キーにモータの速度を指定します。

    ```python
    node_manager.send_command("motor",
        { "command": "set-left-speed-imm", "speed": 9000 })
    ```

- set-right-speed-immコマンド

    右側のモータの速度を設定します。`command`キーには`set-right-speed-imm`を指定します。set-right-speedのように徐々に速度を変化させていくのではなく、直ちに指定された速度に変更します。`speed`キーにモータの速度を指定します。

    ```python
    node_manager.send_command("motor",
        { "command": "set-right-speed-imm", "speed": 3000 })
    ```

- move-distanceコマンド

    現在の速度を保った状態で、指定された距離(センチメートル)を移動します。移動に必要な時間が計算され、その時間だけ`time.sleep()`メソッドにより待機します。**左右のモータが両方停止している場合には命令は実行されません**。また、**左右のモータの速度は同符号である必要があります**。

    ```python
    node_manager.send_command("motor",
        { "command": "move-distance", "distance": 150 })
    ```

- rotate0コマンド

    ロボットの中心速度(センチメートル毎秒)、旋回半径(センチメートル)、旋回角度(度数法)を指定して、ロボットを回転させます。**回転の終了後、回転開始前の速度に自動的に戻されます**。ロボットの旋回角速度(ラジアン毎秒)、回転に必要な時間(秒)、左右の車輪の回転速度(センチメートル毎秒)が計算されます。**ロボットの旋回半径には正の値を指定します**。

    ```python
    node_manager.send_command("motor",
        { "command": "rotate0", "center_velocity": 30,
          "turning_radius": 100, "turning_angle": 120 })
    ```

- rotate1コマンド

    ロボットの中心速度(センチメートル毎秒)、旋回角度(度数法)、旋回時間(秒)を指定して、ロボットを回転させます。**回転の終了後、回転開始前の速度に自動的に戻されます**。ロボットの旋回角速度(ラジアン毎秒)、旋回半径(センチメートル)、左右の車輪の回転速度(センチメートル毎秒)が計算されます。**ロボットの旋回時間には正の値を指定します**。

    ```python
    node_manager.send_command("motor",
        { "command": "rotate1", "center_velocity": 30,
          "turning_angle": 180, "rotate_time": 5.0 })
    ```

- rotate2コマンド

    現在の速度を保った状態で、ロボットの旋回角度を指定して回転させます。**左右のモータの速度は同符号である必要があります**。また、**左右のモータの速度には500以上の差がなくてはならず**、**回転にかかる時間の予想が60秒未満である必要があります**。

    ```python
    node_manager.send_command("motor",
        { "command": "rotate2", "turning_angle": 120 })
    ```

- pivot-turnコマンド

    ロボットの旋回角度(度数法)、旋回時間(秒)を指定して、ロボットの信地旋回(ピボットターン)を行います。信地旋回とは、片方の車輪を止め、もう片方の車輪を動作させることで、ロボット全体を回転させることです。実装では、左の車輪を停止させた状態で右の車輪を回転させています。**回転の終了後、回転開始前の速度に自動的に戻されます**。**旋回時間には正の値を指定します**。

    ```python
    node_manager.send_command("motor",
        { "command": "pivot-turn", "turning_angle": 120, "rotate_time": 5.0 })
    ```

- spin-turnコマンド

    ロボットの旋回角度(度数法)、旋回時間(秒)を指定して、ロボットの超信地旋回(極地旋回)(スピンターン)を行います。超信地旋回とは、左右の車輪を互いに等速逆回転させることで、ロボット全体を回転させることです。**回転の終了後、回転開始前の速度に自動的に戻されます**。**旋回時間には正の値を指定します**。

    ```python
    node_manager.send_command("motor",
        { "command": "spin-turn", "turning_angle": 90, "rotate_time": 3.0 })
    ```

- waitコマンド

    モータの状態を指定された時間だけ一定に保ちます。ロボットを一定の速度で走行させたい場合に使用します。内部では`time.sleep()`メソッドを呼び出して、モータを操作するプロセスの実行を一時的に止めています。`command`キーには`wait`を指定します。`seconds`キーに待ち時間を指定します。

    ```python
    node_manager.send_command("motor", { "command": "wait", "seconds": 3.0 })
    ```

- stopコマンド

    両側のモータの速度を0にしてロボットを止めます。`command`キーに`stop`を指定します。

    ```python
    node_manager.send_command("motor", { "command": "stop" })
    ```

- endコマンド

    モータの使用を停止します。このコマンドを実行した後は、他のコマンドをモータに送信しても作動しません。

    ```python
    node_manager.send_command("motor", { "command": "end" })
    ```

- sequentialコマンド

    複数のコマンドを連続実行させます。コマンドの実行開始時と、全てのコマンドの実行終了時にメッセージがノードから送出されます。個々のコマンドの実行開始時と実行終了時にはメッセージは送出されません。`command`キーには`sequential`を、`sequential`キーには上記のコマンドのリスト(タプルでも可能)をそれぞれ指定します。以下のようなコマンドを送信すると、ロボットはある速度に達するまで徐々に加速した後、3秒間一定の速度で走行し、左にカーブし、続いて右にカーブし、最後に徐々に減速して停止します。

    ```python
    node_manager.send_command("motor",
        { "command": "sequential",
          "sequence": [
            { "command": "set-speed", "speed_left": 9000, "speed_right": 9000,
              "step_left": 100, "step_right": 100, "wait_time": 0.05 },
            { "command": "wait", "seconds": 3.0 },
            { "command": "set-left-speed", "speed": 3000, "step": 100, "wait_time": 0.02 },
            { "command": "set-left-speed", "speed": 9000, "step": 100, "wait_time": 0.02 },
            { "command": "set-right-speed", "speed": 1500, "step": 500, "wait_time": 0.03 },
            { "command": "set-right-speed", "speed": 9000, "step": 300, "wait_time": 0.03 },
            { "command": "set-speed", "speed_left": 0, "speed_right": 0,
              "step_left": 100, "step_right": 100, "wait_time": 0.05 }
          ]
        })
    ```

#### ノードからアプリケーションに送られるメッセージ

ノードからは次のようなメッセージがアプリケーションに送信されます(`NodeManaget.get_msg_queue()`メソッドで取得可能なキューに追加されます)。

- 命令の実行開始

    モータへの命令の実行が開始されたことを表します。

    ```python
    { "sender": "motor", "content": { "command": (実行されたコマンド名), "state": "start" } }
    ```

- 命令の実行無視

    モータへの命令の実行が無視されたことを表します。コマンドが不正であったり、コマンドに渡す値が不正である場合は無視されます。

    ```python
    { "sender": "motor", "content": { "command": (無視されたコマンド名), "state": "ignored" } }
    ```

- 命令の実行終了

    モータへの命令の実行が終了したことを表します。例えば`command`キーに`end`が設定されている場合、モータの使用を停止したことを表すので、その時点でアプリケーションを終了させることができます。

    ```python
    { "sender": "motor", "content": { "command": (実行されたコマンド名), "state": "done" } }
    ```

アプリケーションからは次のようにしてメッセージを取得できます。アプリケーションでは`get()`メソッドではなく、`get_nowait()`メソッドを使用してください。

```python
msg_queue = node_manager.get_msg_queue()

while True:
    if not msg_queue.empty():
        try:
            # ノードからアプリケーションへのメッセージを取得
            msg = msg_queue.get_nowait()
        except queue.Empty:
            time.sleep(0.1)
            continue
    else:
        time.sleep(0.1)
        continue

    if msg["sender"] == "motor":
        # モータの命令を処理
        handle_motor_message(msg["content"])
```

### `ServoMotorNode`クラス

`CommandReceiverNode`クラスを継承しており、アプリケーションからの指示に従ってサーボモータを動作させます。

#### 共有変数の内容

- `state_dict["angle"]`

    - サーボモータの現在の角度を格納します(正確には、値指定のメッセージを実行しても更新されません)。

#### アプリケーションからノードに送られるメッセージ

アプリケーションからは次のような命令を送信できます(変更される可能性が高いです)。

- 値の指定

    指定した値をPWMレジスタに書き込みます。

    ```python
    node_manager.send_command("servo", { "value": 85 })
    ```

- 角度の指定

    指定した角度に設定します(サーボモータごとに指定すべき値が異なります)。

    ```python
    node_manager.send_command("servo", { "angle": 135 })
    ```

#### ノードからアプリケーションに送られるメッセージ

- 命令の実行開始
    
    サーボモータへの命令の実行が開始されたことを表します。

    ```python
    { "sender": "servo", "content": { "command": { "angle": 135 }, "state": "start" } }
    { "sender": "servo", "content": { "command": { "value": 85 }, "state": "start" } }
    ```

- 命令の実行終了

    サーボモータへの命令の実行が終了したことを表します。

    ```python
    { "sender": "servo", "content": { "command": { "angle": 135 }, "state": "done" } }
    { "sender": "servo", "content": { "command": { "value": 85 }, "state": "done" } }
    ```

### `Srf02Node`クラス

`DataSenderNode`クラスを継承しており、超音波センサからの入力値を元に共有変数`state_dict`を更新し続けます。また、障害物への接近を検出した場合はアプリケーションにメッセージを送ります。

#### 共有変数の内容

- `state_dict[アドレス]`
    
    各アドレスを持つ超音波センサで計測された距離情報で、以下のようなディクショナリとなっています。`near`キーには、連続して障害物に接近したと判定されている回数が格納されます。障害物に接近したと判定するための距離の閾値が15cmであったとすると、計測値(指数移動平均により平滑化されています)が15cmを何回連続して下回っているかを表します。5回以上連続して下回っている場合、アプリケーションに向けてメッセージが送信されます。

    ```python
    { "dist": 30, "mindist": 12, "near": 3 }
    ```

#### ノードからアプリケーションに送られるメッセージ

- 障害物接近

    計測値が閾値を連続して下回っており、障害物に接近したと判定された場合に送信されます。

    ```python
    { "sender": "srf02", "content": { "addr": (アドレス), "state": "obstacle-detected" } }
    ```

### `JuliusNode`クラス

`DataSenderNode`クラスを継承しており、認識された文章をアプリケーションに送信し続けます。

#### ノードからアプリケーションに送られるメッセージ

- 認識

    辞書に登録された語彙を認識した場合に送信されます。`direction`キーには方向を示す語彙とその正確度、`command`キーには命令を示す語彙とその正確度のタプルがそれぞれ格納されます。

    ```python
    {
        "sender": "julius",
        "content": {
            "words": [語彙と正確度(0.0から1.0)のタプルのリスト],
            "direction": ("左"または"右", 正確度),
            "command": ("進め/ブレーキ/ストップ/黙れ/曲がれ", 正確度)
        }
    }
    ```

### `OpenJTalkNode`クラス

`CommandReceiverNode`クラスを継承しており、指定された文章を喋らせます。

#### アプリケーションからノードに送られるメッセージ

- 音声ファイルの実行(ファイル名を指定)

    `file_name`キーで指定された音声ファイルを`aplay --quiet`コマンドにより実行します。音声ファイルは、`audio`ディレクトリ(`robot_lib`と同じ階層)の中に保存されている必要があります。**こちらのメッセージの利用を推奨します**。
    
    ```python
    node_manager.send_command("openjtalk", { "file_name": "hello.wav" })
    ```

- 音声合成の実行(文章を指定)

    `sentence`キーで指定された文章を喋らせます。予め用意されたスクリプトファイル(`scripts/openjtalk-start.sh`)を実行して、最初に`openjtalk`コマンドにより`sentence`キーで指定された文章から音声ファイルを生成します。次に、生成されたファイルを`aplay --quiet`コマンドにより再生します。音声合成にある程度の時間(2、3秒)が掛かるため、音声合成の命令の発行から、音声ファイルの再生にまでタイムラグが生じます。ファイル名を直接指定した方が、命令の発行から音声ファイルの再生までに要する時間が短いため、リアルタイム性がより高くなります(例えば、ロボットと会話するアプリケーションでは反応が早くなります)。

    ```python
    node_manager.send_command("openjtalk", { "sentence": "こんにちは" })
    ```

#### ノードからアプリケーションに送られるメッセージ

- 音声ファイルの実行開始

    指定された音声ファイルの再生が開始したことを表します。

    ```python
    { "sender": "openjtalk", "content": { "file_name": (再生された音声ファイル名), "state": "start" } }
    ```

- 音声ファイルの実行終了

    指定された音声ファイルの再生が終了したことを表します。

    ```python
    { "sender": "openjtalk", "content": { "file_name": (再生された音声ファイル名), "state": "done" } }
    ```

- 音声合成の開始

    指定された文章の合成が開始したことを表します。

    ```python
    { "sender": "openjtalk", "content": { "sentence": (指定された文章), "state": "start" } }
    ```

- 音声合成の終了

    指定された文章の合成と音声ファイルの再生が終了したことを表します。

    ```python
    { "sender": "openjtalk", "content": { "sentence": (指定された文章), "state": "done" } }
    ```

### `GoogleSpeechApiNode`クラス

`DataSenderNode`クラスを継承しており、認識された文章をアプリケーションに送信し続けます。**使用はお勧めしません**。

#### ノードからアプリケーションに送られるメッセージ

- 認識

    何らかの文章を認識した場合に送信されます。`direction`キーには方向を示す語彙、`command`キーには命令を示す語彙と、全体の文章の正確性のタプルがそれぞれ格納されます。正確度は個々の語彙に対してではなく文章に対して与えられるため、各語彙の正確度は全て同一の値となっています。

    ```python
    {
        "sender": "speechapi",
        "content": {
            "transcript": (認識された文章),
            "words": [語彙と正確度(0.0から1.0)のタプルのリスト],
            "direction": ("左"または"右", 正確度),
            "command": ("進め/ブレーキ/ストップ/黙れ/曲がれ", 正確度)
        }
    }
    ```

### `WebCamNode`クラス

#### ノードからアプリケーションに送られるメッセージ

- 認識された

    ウェブカメラでキャプチャされた画像から顔が検出された場合に送信されます。`faces`キーには、検出された顔の矩形領域のx座標(px)、y座標(px)、横幅(px)、縦幅(px)のタプルのリストが格納されています。

    ```
    {
        "sender": "webcam",
        "content": {
            "state": "face-detected",
            "faces": [(x0, y0, w0, h0), (x1, y1, w1, h1), ...]
        }
    }
    ```

- 認識されなかった

    ウェブカメラでキャプチャされた画像から顔が検出されなかった場合に送信されます。`faces`キーには空のリストが設定されます。

    ```
    { "sender": "webcam", "content": { "state": "face-not-detected", "faces": [] } }
    ```

### `CardDetectionNode`クラス

#### アプリケーションからノードに送られるメッセージ

- トランプカードの認識

    ウェブカメラに映るトランプカードの数字を認識します。結果の取得までには数秒程度の時間が必要です。

    ```
    node_manager.send_command("card", { "command": "detect" })
    ```

#### ノードからアプリケーションに送られるメッセージ

- トランプカードの認識開始

    トランプカードの認識処理を開始したことを表します。

    ```
    { "sender": "card", "content": { "command": "detect", "state": "start" } }
    ```

- トランプカードの認識終了

    トランプカードの認識処理が終了したことを表します。`cards`キーには、認識されたトランプカードの数字のリストが格納されています。

    ```
    {
        "sender": "card",
        "content": {
            "command": "detect",
            "state": "detected",
            "cards": (認識された数字のリスト)
        }
    }
    ```

- 命令の実行無視

    ノードへの命令の実行が無視されたことを表します。`command`キーに指定するコマンド名が不正である場合に送出されます。

    ```
    { "sender": "card", "content": { "command": (無視されたコマンド名), "state": "ignored" } }
    ```

