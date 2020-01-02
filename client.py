import threading
import logging

import grpc

import grpc_chat_pb2
import grpc_chat_pb2_grpc


def run():
    # サーバーに接続
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = grpc_chat_pb2_grpc.GrpcChatStub(channel)

        # サインイン
        while True:
            select = input('Sign Up: 1\nSign in: 2\n>')
            if select == '1':
                # サインアップ
                token = stub.Register(grpc_chat_pb2.AuthRequest(
                    username=input(), password=input())).token
                break
            elif select == '2':
                # サインイン
                token = stub.Auth(grpc_chat_pb2.AuthRequest(
                    username=input(), password=input())).token
                break

        # メッセージを取得する関数
        def GetStreamMessage():
            responses = stub.GetStreamMessage(
                grpc_chat_pb2.GetStreamMessageRequest(token=token))
            for response in responses:
                print(response.text)

        # メッセージを送信する関数
        def PostMessage():
            while True:
                stub.PostMessage(grpc_chat_pb2.PostMessageRequest(
                    token=token, text=input('>')))

        # 並列に実行
        GetStreamMessageThread = threading.Thread(target=GetStreamMessage)
        GetStreamMessageThread.start()
        PostMessage()


if __name__ == '__main__':
    logging.basicConfig()
    run()
