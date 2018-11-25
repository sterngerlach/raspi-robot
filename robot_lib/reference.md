
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

ノードの状態を格納するディクショナリを初期化します。各ノードは必要に応じてこのメソッドをオーバーライドすることができます。

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

`process_handler`を初期化するためにコンストラクタ内で呼び出されます。

- `update()`

入力を処理して、`Node.send_message()`メソッドによりアプリケーションにメッセージを送信したり、`Node.state_dict`を必要に応じて更新したりするためのメソッドです。`DataSenderNode`クラスを継承したクラスではこのメソッドをオーバーライドします。

- `run()`

`update()`メソッドを実行する子プロセスを開始するために、`NodeManager`クラスから呼び出されます。


