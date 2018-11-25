
# robot\_libの説明書き

## 基本的なクラス群

* `Node`クラス
各ノードを表す基底クラス。
    - `process_manager`
    プロセス間で共有するオブジェクトを作成するために利用されるマネージャオブジェクト(`multiprocessing.managers.SyncManager`クラスのインスタンス)です。`multiprocessing.Manager()`メソッドにより作成されます。

    - `state_dict`
    ノードの状態を格納するためのディクショナリで、各ノードとアプリケーションの間で共有されています。`dict`オブジェクトのプロキシで、`multiprocessing.managers.SyncManager.dict()`メソッドにより作成されます。各ノードでは`state_dict`に自由な項目を追加することができます(アプリケーションがその項目を参照します)。

    - `msg_queue`
    各ノードからアプリケーションへのメッセージを格納するキューで、全ノード間で共有されています。`queue.Queue`オブジェクトのプロキシで、`multiprocessing.managers.SyncManager.Queue()`メソッドにより作成されます。`send_message()`メソッドによってノードからアプリケーションに向けてメッセージを送ることができます。

    - `__init__()`
    ノードを初期化します。

    - `initialize_state_dict()`
    ノードの状態を格納するディクショナリを初期化します。

    - `run()`
    ノードの実行を開始します(抽象メソッドであるため呼び出すことはできません)。

    - `send_message(sender_name, msg)`
    ノードからアプリケーションに向けてメッセージを送信します。引数`sender_name`はメッセージの送り主の名前(ID)、引数`msg`はメッセージ(文字列やディクショナリ型)です。メッセージは次のように辞書型に変換された上で、キュー`msg_queue`に追加されます。
    ```python
    { "sender": sender_name, "content": msg }
    ```

