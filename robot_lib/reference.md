
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

- `send_command()`

    命令をキュー`command_queue`に追加します。アプリケーション側のプロセスでこのメソッドを呼び出します。

- `wait_until_all_command_done()`
    
    キューから全ての命令が取り出されて空になるまで実行をブロックします。アプリケーション側のプロセスでこのメソッドを呼び出します。

- `run()`

    命令を実行する子プロセスを開始するために、`NodeManager`クラスから呼び出されます。アプリケーション側で呼び出す場合があります。

- `terminate()`

    命令を実行する子プロセスを強制終了させるために、アプリケーション側のプロセスで呼び出すことができます。プロセスを強制終了すると、実行途中の命令は中断されます。また、`initialize_state_dict()`メソッドが呼び出されるので、ノードの状態を保持するディクショナリは初期化されます。更に、`initialize_command_queue()`メソッドが呼び出されてキュー`command_queue`が初期化されるため、強制終了時にキュー`command_queue`内に残っていた未実行の命令は全て破棄され、実行されることはありません。`initialize_process_handler()`メソッドの呼び出しによって、再びノードの実行を開始できるようになります(`run()`メソッドの呼び出しが可能になる)。


