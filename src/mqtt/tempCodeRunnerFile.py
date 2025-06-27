   def on_connect(self, client, userdata, flags, rc):
        # 获取客户端socket信息
        sock = self.client._socket
        if sock:
            try:
                peer = sock.getpeername()
                print(f"客户端已连接 | IP: {peer[0]} | Port: {peer[1]}")
            except Exception as e:
                print(f"获取客户端信息失败: {str(e)}")