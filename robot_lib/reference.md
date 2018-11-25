
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

    ```python
    config = {
        "enable_motor": True,       # 左右のモータを有効化
        "enable_servo": True,       # サーボモータを有効化
        "enable_srf02": True,       # 超音波センサを有効化
        "enable_julius": True,      # 音声認識エンジンJuliusのノードを有効化
        "enable_openjtalk": True,   # 音声合成システムOpenJTalkのノードを有効化
        "enable_speechapi": False,  # 音声認識(Google Cloud Speech API)を有効化
        "enable_webcam": True,      # 人の顔を認識するウェブカメラを有効化

        "motor": {},                # モータの設定(特に設定内容は無いため空のディクショナリを指定)
        "servo": {},                # サーボモータの設定(特になし)
        "srf02": {
            "near_obstacle_threshold": 15,  # 障害物接近を判定するための距離の閾値
            "interval": 0.25,               # 距離の計測を行う間隔(秒)
            "addr_list": [0x70, 0x71]       # 超音波センサのアドレスのリスト
        },
        "julius": {},               # Juliusの設定(特になし)
        "openjtalk": {},            # OpenJTalkの設定(特になし)
        "speechapi": {},            # Google Speech APIの設定(特になし)
        "webcam": {}                # ウェブカメラの設定(特になし)
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

`CommandReceiverNode`クラスを継承しており、アプリケーションからの指示に従って左右のモータを実際に動作させます。アプリケーションからは次のような命令を送信できます(変更される可能性が高いです)。

- accelコマンド

    左右両方のモータを指定の速度まで加速させます(`command`キーに`accel`を指定)。`speed`キーに速度、`wait_time`に適当な待ち時間を設定します(待ち時間を小さくすると加速が急になります)。

    ```python
    node_manager.send_command("motor",
        { "command": "accel", "speed": 9000, "wait_time": 0.06 })
    ```
    
    以下のように、1回のループの実行で速度が250ずつ増えるように実装されています。`wait_time`は各ループの実行後の待ち時間です。速度には250で割り切れるような値を設定してください。

    ```python
    def accelerate(self, speed, wait_time):
        """2つのモータを加速"""
        
        while self.state_dict["speed_left"] < speed:
            self.state_dict["speed_left"] += 250
            self.state_dict["speed_right"] += 250

            self.motor_left.run(self.state_dict["speed_left"])
            self.motor_right.run(-self.state_dict["speed_right"])

            time.sleep(wait_time)
    ```

- accel-leftコマンド

    左側のモータを指定の速度まで回転させます(`command`キーに`accel-left`を指定)。速度には250で割り切れるような値を設定してください。

    ```python
    node_manager.send_command("motor",
        { "command": "accel-left", "speed": 9000, "wait_time": 0.06 })
    ```

- accel-rightコマンド

    右側のモータを指定の速度まで回転させます(`command`キーに`accel-right`を指定)。速度には250で割り切れるような値を設定してください。

    ```python
    node_manager.send_command("motor",
        { "command": "accel-right", "speed": 9000, "wait_time": 0.06 })
    ```

- brakeコマンド

    左右両方のモータを指定の速度まで減速させます(`command`キーに`brake`を指定)。速度には250で割り切れるような値を設定してください。

    ```python
    node_manager.send_command("motor",
        { "command": "brake", "speed": 3000, "wait_time": 0.06 })
    ```

- brake-leftコマンド

    左側のモータを指定の速度まで減速させます(`command`キーに`brake-left`を指定)。速度には250で割り切れるような値を設定してください。

    ```python
    node_manager.send_command("motor",
        { "command": "brake-left", "speed": 3000, "wait_time": 0.06 })
    ```

- brake-rightコマンド

    右側のモータを指定の速度まで減速させます(`command`キーに`brake-right`を指定)。速度には250で割り切れるような値を設定してください。

    ```python
    node_manager.send_command("motor",
        { "command": "brake-right", "speed": 3000, "wait_time": 0.06 })
    ```

- stopコマンド

    両側のモータの速度を0にてロボットを止めます(`command`キーに`stop`を指定)。

    ```python
    node_manager.send_command("motor", { "command": "stop" })
    ```

- endコマンド

    モータの使用を停止します。このコマンドを実行すると、他のコマンドをモータに送信してもモータは動かなくなります。

    ```python
    node_manager.send_command("motor", { "command": "end" })
    ```

- rotateコマンド

    ロボットが停止した状態から時計回り、半時計回りに90度回転します。ロボットの走行時にはこのコマンドを使用してはいけません。`command`キーに`rotate`を指定し、`direction`キーには`left`(半時計回り)または`right`(時計回り)を指定します。`wait_time`キーに待ち時間を設定した場合、値を大きくすると回転量が大きく、値を小さくすると回転量が小さくなるので、回転量を微調節することができます。`wait_time`キーを使用しない場合は既定値(1.5秒)が利用されます。

    ```python
    node_manager.send_command("motor", { "command": "rotate", "direction": "left" })
    ```

