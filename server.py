from concurrent import futures
import logging
import queue
import time
import secrets
import bcrypt

import grpc
import jwt

import grpc_chat_pb2
import grpc_chat_pb2_grpc


class GrpcChat(grpc_chat_pb2_grpc.GrpcChatServicer):
    def __init__(self):
        # ユーザーごとのJWTのシークレットキーを格納する辞書
        self.secret_key = secrets.token_urlsafe()
        # ユーザーとパスワードを格納する辞書
        self.password = {}
        # ユーザーに送信するメッセージのキューを格納する辞書
        self.message_queue = {}

    # JWTのエンコード
    def __encode(self, payload):
        return jwt.encode(payload, self.secret_key, algorithm='HS256')

    # JWTのデコード
    def __decode(self, token):
        return jwt.decode(token, self.secret_key, algorithm='HS256')

    # JWTの生成
    def __generate_jwt(self, username):
        return self.__encode({'user': username})

    # ユーザーを登録
    def Register(self, request, context):
        try:
            # ユーザー名が未取得であればユーザーを登録
            if request.username not in self.password:
                # パスワードをハッシュ化
                self.password[request.username] = bcrypt.hashpw(
                    request.password.encode('utf-8'), bcrypt.gensalt())

                # ユーザーに送信するメッセージのキューの作成
                self.message_queue[request.username] = queue.Queue()
            else:
                context.abort(grpc.StatusCode.ALREADY_EXISTS,
                              'That username is taken.')

            return grpc_chat_pb2.AuthResponse(token=self.__generate_jwt(request.username))

        except:
            context.abort(grpc.StatusCode.UNKNOWN, 'Unkown error.')

    # ユーザーの認証
    def Auth(self, request, context):
        try:
            # パスワードが同じであれば
            if bcrypt.checkpw(request.password.encode('utf-8'), self.password[request.username]):
                return grpc_chat_pb2.AuthResponse(token=self.__generate_jwt(request.username))
            else:
                context.abort(grpc.StatusCode.UNAUTHENTICATED,
                              'Wrong password.')

        except:
            context.abort(grpc.StatusCode.UNKNOWN, 'Unkown error.')

    # ユーザーからメッセージを取得
    def PostMessage(self, request, context):
        try:
            # ユーザー名をJWTから取得
            current_user = self.__decode(request.token)['user']

            # すべてのユーザーのキューに新規メッセージを追加
            print(current_user, request.text)
            for user in self.message_queue:
                self.message_queue[user].put(
                    grpc_chat_pb2.GetStreamMessageResponse(user=current_user, text=request.text))

            return grpc_chat_pb2.PostMessageResponse(ok=True)

        except:
            context.abort(grpc.StatusCode.UNKNOWN, 'Unkown error.')

    # ユーザーにメッセージを送信
    def GetStreamMessage(self, request, context):
        # ユーザー名をJWTから取得
        current_user = self.__decode(request.token)['user']

        while True:
            # キューにメッセージがあれば送信
            if self.message_queue[current_user].empty():
                pass
            else:
                yield self.message_queue[current_user].get()


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    grpc_chat_pb2_grpc.add_GrpcChatServicer_to_server(GrpcChat(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    serve()
