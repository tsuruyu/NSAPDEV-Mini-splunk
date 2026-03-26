import socket
import threading
import sys
from datetime import datetime

import MOD_READ
import MOD_QUERY
import MOD_ADMIN

HOST         = "0.0.0.0"
DEFAULT_PORT = 1337

def log(addr: tuple, message: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{addr[0]}:{addr[1]}] {message}")


def describe_command(raw: str) -> str:
    parts    = raw.split("|", 2)
    cmd_type = parts[0].strip().upper() if parts else ""

    if cmd_type == "UPLOAD" and len(parts) >= 2:
        return f"INGEST {parts[1].strip()}"

    elif cmd_type == "QUERY" and len(parts) >= 3:
        sub = parts[1].strip().upper()
        arg = parts[2].strip()
        return f"QUERY {sub} \"{arg}\""

    elif cmd_type == "ADMIN" and len(parts) >= 2:
        return f"ADMIN {parts[1].strip().upper()}"

    elif cmd_type == "DISCONNECT":
        return "DISCONNECT"

    return f"UNKNOWN \"{raw[:60]}\""


def dispatch(message: str) -> str:
    parts    = message.split("|", 2)
    cmd_type = parts[0].strip().upper() if parts else ""

    if cmd_type == "UPLOAD":
        if len(parts) < 3:
            return "ERROR: UPLOAD requires a filename and file data."
        return MOD_READ.ingest(parts[2])

    elif cmd_type == "QUERY":
        if len(parts) < 3:
            return "ERROR: QUERY requires a subcommand and argument."
        sub = parts[1].strip().upper()
        arg = parts[2].strip()
        if sub == "SEARCH_DATE":
            return MOD_QUERY.search_date(arg)
        elif sub == "SEARCH_HOST":
            return MOD_QUERY.search_host(arg)
        elif sub == "SEARCH_DAEMON":
            return MOD_QUERY.search_daemon(arg)
        elif sub == "SEARCH_SEVERITY":
            return MOD_QUERY.search_severity(arg)
        elif sub == "SEARCH_KEYWORD":
            return MOD_QUERY.search_keyword(arg)
        elif sub == "COUNT_KEYWORD":
            return MOD_QUERY.count_keyword(arg)
        else:
            return f"ERROR: Unknown QUERY subcommand '{sub}'."

    elif cmd_type == "ADMIN":
        if len(parts) < 2:
            return "ERROR: ADMIN requires a subcommand."
        sub = parts[1].strip().upper()
        if sub == "PURGE":
            return MOD_ADMIN.purge()
        else:
            return f"ERROR: Unknown ADMIN subcommand '{sub}'."

    else:
        return f"ERROR: Unknown command type '{cmd_type}'."


def recv_all(conn: socket.socket) -> str | None:
    buffer = b""
    while True:
        try:
            chunk = conn.recv(65536)
        except OSError:
            return None

        if not chunk:
            return None

        buffer += chunk
        if buffer.endswith(b"<<END>>"):
            return buffer[: -len(b"<<END>>")].decode("utf-8", errors="replace")


def handle_client(conn: socket.socket, addr: tuple):
    log(addr, "Connection accepted.")
    try:
        while True:
            raw = recv_all(conn)

            if raw is None:
                log(addr, "Client disconnected abruptly (process killed or network dropped).")
                break

            raw = raw.strip()

            if not raw:
                continue

            cmd_label = describe_command(raw)
            log(addr, f"Command received: {cmd_label}")

            if raw.split("|", 1)[0].strip().upper() == "DISCONNECT":
                log(addr, "Client sent EXIT. Closing connection.")
                conn.sendall(("BYE\n<<END>>").encode("utf-8"))
                break

            response = dispatch(raw)
            conn.sendall((response + "\n<<END>>").encode("utf-8"))
            log(addr, f"Response sent for: {cmd_label}")

    except Exception as ex:
        log(addr, f"Unexpected error: {ex}")
    finally:
        conn.close()
        log(addr, "Connection closed.")


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
            log(addr, "Spawned worker thread.")
    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down.")
    finally:
        server_sock.close()


if __name__ == "__main__":
    main()