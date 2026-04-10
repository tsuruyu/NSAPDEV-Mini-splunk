# NSAPDEV "Mini-Splunk" Syslog Analytics Server

## Running the program
1. On two separate terminals:
```bash
python3 server.py
```
```bash
python3 client.py
```

2. You can issue commands from the client window. INGEST files from `log_files\` first before querying.
```bash
client> INGEST log_files\SVR1_server_auth_syslog.txt 0.0.0.0:1337
```

## Usage
```
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

  ADMIN <IP>:<Port> PURGE
      Clear all indexed log entries on the server.

  HELP  — Show this help text.
  CLEAR — Clear the terminal and redisplay the banner.
  EXIT  — Disconnect from server and quit.
──────────────────────────────────────────────────────────
```
