import socket
import threading
import sys

import read
import query
import admin

HOST = "0.0.0.0"
DEFAULT_PORT = 65432

def dispatch(message: str) -> str:
    parts    = message.split("|", 2)
    cmd_type = parts[0].strip().upper() if parts else ""

    if cmd_type == "UPLOAD":
        if len(parts) < 3:
            return "ERROR: UPLOAD requires a filename and file data."
        return read.ingest(parts[2])

    elif cmd_type == "QUERY":
        if len(parts) < 3:
            return "ERROR: QUERY requires a subcommand and argument."
        sub = parts[1].strip().upper()
        arg = parts[2].strip()
        if sub == "SEARCH_DATE":
            return query.search_date(arg)
        elif sub == "SEARCH_HOST":
            return query.search_host(arg)
        elif sub == "SEARCH_DAEMON":
            return query.search_daemon(arg)
        elif sub == "SEARCH_SEVERITY":
            return query.search_severity(arg)
        elif sub == "SEARCH_KEYWORD":
            return query.search_keyword(arg)
        elif sub == "COUNT_KEYWORD":
            return query.count_keyword(arg)
        else:
            return f"ERROR: Unknown QUERY subcommand '{sub}'."

    elif cmd_type == "ADMIN":
        if len(parts) < 2:
            return "ERROR: ADMIN requires a subcommand."
        sub = parts[1].strip().upper()
        if sub == "PURGE":
            return admin.purge()
        else:
            return f"ERROR: Unknown ADMIN subcommand '{sub}'."

    else:
        return f"ERROR: Unknown command type '{cmd_type}'."


def recv_all(conn: socket.socket) -> str:
    buffer = b""
    while True:
        chunk = conn.recv(65536)
        if not chunk:
            break
        buffer += chunk
        if buffer.endswith(b"<<END>>"):
            buffer = buffer[: -len(b"<<END>>")]
            break
    return buffer.decode("utf-8", errors="replace")


def handle_client(conn: socket.socket, addr: tuple):
    print(f"[SERVER] Connection accepted from {addr[0]}:{addr[1]}")
    try:
        while True:
            raw = recv_all(conn)
            if not raw:
                break
            response = dispatch(raw.strip())
            conn.sendall((response + "\n<<END>>").encode("utf-8"))
    except (ConnectionResetError, BrokenPipeError):
        print(f"[SERVER] Client {addr[0]}:{addr[1]} disconnected abruptly.")
    except Exception as ex:
        print(f"[SERVER] Error handling client {addr[0]}:{addr[1]}: {ex}")
    finally:
        conn.close()
        print(f"[SERVER] Connection closed for {addr[0]}:{addr[1]}")


def main():
    port        = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, port))
    server_sock.listen(10)
    print(f"[SERVER] Indexer listening on {HOST}:{port}")

    try:
        while True:
            conn, addr = server_sock.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
            print(f"[SERVER] Spawned worker thread for {addr[0]}:{addr[1]}")
    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down.")
    finally:
        server_sock.close()


if __name__ == "__main__":
    main()