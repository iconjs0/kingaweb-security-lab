"""Loopback TCP relays: learner Burp/curl reaches 127.0.0.1:PORT, relay forwards
into the session's internal network. Session nets stay internal (no egress);
only the trusted orchestrator bridges host-loopback to container IPs. stdlib only."""
import socket
import socketserver
import threading

class _Handler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        try:
            up = socket.create_connection((self.server.up_ip, self.server.up_port), timeout=5)
        except Exception:
            return
        down = self.request
        down.settimeout(60)
        up.settimeout(60)

        def fwd(src: socket.socket, dst: socket.socket) -> None:
            try:
                while True:
                    chunk = src.recv(65536)
                    if not chunk:
                        break
                    dst.sendall(chunk)
            except Exception:
                pass

        t = threading.Thread(target=fwd, args=(up, down), daemon=True)
        t.start()
        fwd(down, up)
        for s in (up, down):
            try:
                s.close()
            except Exception:
                pass

class Relay(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

def start(listen_host: str, up_ip: str, up_port: int) -> tuple[Relay, int]:
    srv = Relay((listen_host, 0), _Handler)
    srv.up_ip, srv.up_port = up_ip, up_port  # type: ignore[attr-defined]
    threading.Thread(target=srv.serve_forever, kwargs={"poll_interval": 0.2}, daemon=True).start()
    return srv, srv.server_address[1]

def stop(srv: Relay) -> None:
    try:
        srv.shutdown()
    except Exception:
        pass
    try:
        srv.server_close()
    except Exception:
        pass
