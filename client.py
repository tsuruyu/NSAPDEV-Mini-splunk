import socket
import os
import sys
import glob
import readline

BANNER = """
╔══════════════════════════════════════════════════════════╗
║   Welcome to the "Mini-Splunk" Syslog Analytics Server   ║
║                NSAPDEV  |  Baradas & Loja                ║
╚══════════════════════════════════════════════════════════╝
Type HELP to list available commands. Type EXIT to quit.
"""

HELP_TEXT = """
Available Commands
──────────────────────────────────────────────────────────
  INGEST <file_path> <IP>:<Port>
      Upload a local syslog file to the server.

  QUERY <IP>:<Port> SEARCH_DATE "<date_string>"
      Search indexed logs by date  (e.g. "Feb 7").

  QUERY <IP>:<Port> SEARCH_HOST <hostname>
      Search indexed logs by originating hostname.

  QUERY <IP>:<Port> SEARCH_DAEMON <daemon>
      Search indexed logs by daemon/process name.

  QUERY <IP>:<Port> SEARCH_SEVERITY <level>
      Search indexed logs by severity level.
      Levels: EMERG, ALERT, CRIT, ERR, WARNING, NOTICE, INFO, DEBUG

  QUERY <IP>:<Port> SEARCH_KEYWORD <keyword>
      Search indexed logs whose message contains a keyword.

  QUERY <IP>:<Port> COUNT_KEYWORD <keyword>
      Count how many log entries contain a keyword.

  PURGE <IP>:<Port>
      Clear all indexed log entries on the server.

  HELP  — Show this help text.
  CLEAR — Clear the terminal and redisplay the banner.
  EXIT  — Disconnect from server and quit.
──────────────────────────────────────────────────────────
"""


class Session:
    def __init__(self):
        self._sock: socket.socket | None = None
        self._addr: tuple[str, int] | None = None

    def connect(self, host: str, port: int):
        if self._sock and self._addr == (host, port):
            return
        if self._sock:
            self._sock.close()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        self._sock = s
        self._addr = (host, port)
        print(f"[System Message] Connected to {host}:{port}")

    def send(self, payload: str) -> str:
        self._sock.sendall((payload + "<<END>>").encode("utf-8"))

        buffer = b""
        while True:
            chunk = self._sock.recv(65536)
            if not chunk:
                raise ConnectionResetError("Server closed the connection unexpectedly.")
            buffer += chunk
            if buffer.endswith(b"\n<<END>>"):
                buffer = buffer[: -len(b"\n<<END>>")]
                break

        return buffer.decode("utf-8", errors="replace").strip()

    def disconnect(self):
        if self._sock:
            try:
                self._sock.sendall(("DISCONNECT||<<END>>").encode("utf-8"))
                self._sock.recv(1024)
            except OSError:
                pass
            finally:
                self._sock.close()
                self._sock = None
                self._addr = None

    @property
    def connected(self) -> bool:
        return self._sock is not None


session = Session()


def path_completer(text: str, state: int):
    expanded = os.path.expanduser(text)

    if os.path.isdir(expanded) and not expanded.endswith(os.sep):
        expanded += os.sep

    matches = glob.glob(expanded + "*")
    matches = [
        (m + os.sep if os.path.isdir(m) else m)
        for m in sorted(matches)
    ]

    if text.startswith("~"):
        home    = os.path.expanduser("~")
        matches = ["~" + m[len(home):] for m in matches]

    try:
        return matches[state]
    except IndexError:
        return None


def parse_address(addr_str: str) -> tuple[str, int]:
    try:
        host, port_str = addr_str.rsplit(":", 1)
        return host.strip(), int(port_str.strip())
    except ValueError:
        raise ValueError(f"Invalid address format '{addr_str}'. Expected <IP>:<Port>.")


def do_send(host: str, port: int, payload: str) -> str | None:
    try:
        session.connect(host, port)
        return session.send(payload)
    except ConnectionRefusedError:
        print(f"[Client Error] Connection refused. Is the server running on {host}:{port}?")
    except (ConnectionResetError, OSError) as e:
        print(f"[Client Error] Connection lost: {e}")
    return None


def cmd_ingest(tokens: list[str]):
    if len(tokens) < 3:
        print("[Client Error] Usage: INGEST <file_path> <IP>:<Port>")
        return

    file_path = tokens[1]
    addr_str  = tokens[2]

    if not os.path.isfile(file_path):
        print(f"[Client Error] File not found: '{file_path}'")
        return

    try:
        host, port = parse_address(addr_str)
    except ValueError as e:
        print(f"[Client Error] {e}")
        return

    file_size  = os.path.getsize(file_path)
    size_label = (
        f"{file_size / 1_048_576:.1f} MB" if file_size >= 1_048_576
        else f"{file_size / 1024:.1f} KB"
    )
    filename = os.path.basename(file_path)

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
            file_data = fh.read()
    except OSError as e:
        print(f"[Client Error] Could not read file: {e}")
        return

    print(f"[System Message] Uploading {filename} ({size_label})...")

    response = do_send(host, port, f"UPLOAD|{filename}|{file_data}")
    if response is not None:
        print(f"[Server Response] {response}")


def cmd_search_date(host: str, port: int, tokens: list[str]):
    if len(tokens) < 4:
        print("[Client Error] Usage: QUERY <IP>:<Port> SEARCH_DATE \"<date_string>\"")
        return

    argument = " ".join(tokens[3:]).strip('"').strip("'")
    print("[System Message] Sending query...")

    response = do_send(host, port, f"QUERY|SEARCH_DATE|{argument}")
    if response is not None:
        print(f"[Server Response] {response}")


def cmd_search_host(host: str, port: int, tokens: list[str]):
    if len(tokens) < 4:
        print("[Client Error] Usage: QUERY <IP>:<Port> SEARCH_HOST <hostname>")
        return

    argument = tokens[3]
    print("[System Message] Sending query...")

    response = do_send(host, port, f"QUERY|SEARCH_HOST|{argument}")
    if response is not None:
        print(f"[Server Response] {response}")


def cmd_search_daemon(host: str, port: int, tokens: list[str]):
    if len(tokens) < 4:
        print("[Client Error] Usage: QUERY <IP>:<Port> SEARCH_DAEMON <daemon>")
        return

    argument = tokens[3]
    print("[System Message] Sending query...")

    response = do_send(host, port, f"QUERY|SEARCH_DAEMON|{argument}")
    if response is not None:
        print(f"[Server Response] {response}")


def cmd_search_severity(host: str, port: int, tokens: list[str]):
    if len(tokens) < 4:
        print("[Client Error] Usage: QUERY <IP>:<Port> SEARCH_SEVERITY <level>")
        return

    argument = tokens[3]
    print("[System Message] Sending query...")

    response = do_send(host, port, f"QUERY|SEARCH_SEVERITY|{argument}")
    if response is not None:
        print(f"[Server Response] {response}")


def cmd_search_keyword(host: str, port: int, tokens: list[str]):
    if len(tokens) < 4:
        print("[Client Error] Usage: QUERY <IP>:<Port> SEARCH_KEYWORD <keyword>")
        return

    argument = " ".join(tokens[3:]).strip('"').strip("'")
    print("[System Message] Sending query...")

    response = do_send(host, port, f"QUERY|SEARCH_KEYWORD|{argument}")
    if response is not None:
        print(f"[Server Response] {response}")


def cmd_count_keyword(host: str, port: int, tokens: list[str]):
    if len(tokens) < 4:
        print("[Client Error] Usage: QUERY <IP>:<Port> COUNT_KEYWORD <keyword>")
        return

    argument = " ".join(tokens[3:]).strip('"').strip("'")
    print("[System Message] Sending query...")

    response = do_send(host, port, f"QUERY|COUNT_KEYWORD|{argument}")
    if response is not None:
        print(f"[Server Response] {response}")


def cmd_purge(host: str, port: int):
    print(f"[System Message] Connecting to {host}:{port} to purge records...")

    response = do_send(host, port, "ADMIN|PURGE")
    if response is not None:
        print(f"[Server Response] {response}")


def cmd_query(tokens: list[str]):
    if len(tokens) < 3:
        print("[Client Error] Usage: QUERY <IP>:<Port> <SUBCOMMAND> [argument]")
        return

    addr_str   = tokens[1]
    subcommand = tokens[2].upper()

    try:
        host, port = parse_address(addr_str)
    except ValueError as e:
        print(f"[Client Error] {e}")
        return

    valid_subcommands = {
        "SEARCH_DATE", "SEARCH_HOST", "SEARCH_DAEMON",
        "SEARCH_SEVERITY", "SEARCH_KEYWORD", "COUNT_KEYWORD",
    }

    if subcommand not in valid_subcommands:
        print(f"[Client Error] Unknown subcommand '{subcommand}'.")
        print(f"               Valid options: {', '.join(sorted(valid_subcommands))}")
        return

    if subcommand == "SEARCH_DATE":
        cmd_search_date(host, port, tokens)
    elif subcommand == "SEARCH_HOST":
        cmd_search_host(host, port, tokens)
    elif subcommand == "SEARCH_DAEMON":
        cmd_search_daemon(host, port, tokens)
    elif subcommand == "SEARCH_SEVERITY":
        cmd_search_severity(host, port, tokens)
    elif subcommand == "SEARCH_KEYWORD":
        cmd_search_keyword(host, port, tokens)
    elif subcommand == "COUNT_KEYWORD":
        cmd_count_keyword(host, port, tokens)


def cmd_purge_new(tokens: list[str]):
    if len(tokens) < 2:
        print("[Client Error] Usage: PURGE <IP>:<Port>")
        return

    addr_str = tokens[1]

    try:
        host, port = parse_address(addr_str)
    except ValueError as e:
        print(f"[Client Error] {e}")
        return

    cmd_purge(host, port)


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")
    print(BANNER)


def repl():
    readline.set_completer(path_completer)
    readline.set_completer_delims(" \t\n")
    readline.parse_and_bind("tab: complete")

    clear_screen()
    while True:
        try:
            raw = input("client> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[System Message] Disconnecting and exiting. Goodbye.")
            session.disconnect()
            sys.exit(0)

        if not raw:
            continue

        tokens  = raw.split()
        command = tokens[0].upper()

        if command == "EXIT":
            print("[System Message] Disconnecting and exiting. Goodbye.")
            session.disconnect()
            sys.exit(0)

        elif command == "CLEAR":
            clear_screen()

        elif command == "HELP":
            print(HELP_TEXT)

        elif command == "INGEST":
            cmd_ingest(tokens)

        elif command == "QUERY":
            cmd_query(tokens)

        elif command == "PURGE":
            cmd_purge_new(tokens)

        else:
            print(f"[Client Error] Unknown command '{command}'. Type HELP for usage.")


if __name__ == "__main__":
    repl()