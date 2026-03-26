import threading
import re

log_store = []

read_count      = 0
read_count_lock = threading.Lock()
write_lock      = threading.Lock()

SYSLOG_PATTERN = re.compile(
    r"^(?P<month>\w{3})\s{1,2}(?P<day>\d{1,2})\s+"
    r"(?P<time>\d{2}:\d{2}:\d{2})\s+"
    r"(?P<hostname>\S+)\s+"
    r"(?P<process>\S+?)(?:\[(?P<pid>\d+)\])?:\s+"
    r"(?P<message>.+)$"
)

SEVERITY_MAP = {
    "emerg": "EMERG", "alert": "ALERT", "crit": "CRIT",
    "error": "ERR",   "err":   "ERR",   "warn": "WARNING",
    "warning": "WARNING", "notice": "NOTICE",
    "info": "INFO",   "debug": "DEBUG",
}


def acquire_read():
    global read_count
    with read_count_lock:
        read_count += 1
        if read_count == 1:
            write_lock.acquire()


def release_read():
    global read_count
    with read_count_lock:
        read_count -= 1
        if read_count == 0:
            write_lock.release()


def infer_severity(message: str) -> str:
    msg_lower = message.lower()
    for keyword, level in SEVERITY_MAP.items():
        if keyword in msg_lower:
            return level
    return "INFO"


def parse_syslog_line(line: str) -> dict | None:
    line = line.strip()
    if not line:
        return None
    match = SYSLOG_PATTERN.match(line)
    if not match:
        return None
    timestamp = f"{match.group('month')} {int(match.group('day')):2d} {match.group('time')}"
    message   = match.group("message")
    return {
        "timestamp": timestamp,
        "hostname":  match.group("hostname"),
        "process":   match.group("process"),
        "pid":       match.group("pid") or "",
        "severity":  infer_severity(message),
        "message":   message,
        "raw":       line,
    }


def format_entry(entry: dict) -> str:
    pid_part = f"[{entry['pid']}]" if entry["pid"] else ""
    return (
        f"{entry['timestamp']} {entry['hostname']} "
        f"{entry['process']}{pid_part}: {entry['message']}"
    )