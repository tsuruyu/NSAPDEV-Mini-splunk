from datetime import datetime
import MOD_STORE as store


def search_date(date_str: str) -> str:
    try:
        target = datetime.strptime(date_str.strip(), "%b %d")
    except ValueError:
        return f"ERROR: Invalid date format '{date_str}'. Expected e.g. 'Feb 22'"

    store.acquire_read()
    try:
        results = []
        for entry in store.log_store:
            try:
                ts_parts = entry["timestamp"].strip().split()
                e_month  = datetime.strptime(ts_parts[0], "%b").month
                e_day    = int(ts_parts[1])
                if e_month == target.month and e_day == target.day:
                    results.append(entry)
            except Exception:
                continue
    finally:
        store.release_read()

    if not results:
        return f"Found 0 matching entries for date '{date_str}'."

    lines = [f"Found {len(results)} matching entries for date '{date_str}':"]
    for i, e in enumerate(results, 1):
        lines.append(f"{i}. {store.format_entry(e)}")
    return "\n".join(lines)


def search_host(hostname: str) -> str:
    store.acquire_read()
    try:
        results = [
            entry for entry in store.log_store
            if entry["hostname"].lower() == hostname.strip().lower()
        ]
    finally:
        store.release_read()

    if not results:
        return f"Found 0 matching entries for host '{hostname}'."

    lines = [f"Found {len(results)} matching entries for host '{hostname}':"]
    for i, e in enumerate(results, 1):
        lines.append(f"{i}. {store.format_entry(e)}")
    return "\n".join(lines)


def search_daemon(daemon: str) -> str:
    # TODO: implement SEARCH_DAEMON
    pass


def search_severity(level: str) -> str:
    # TODO: implement SEARCH_SEVERITY
    pass


def search_keyword(keyword: str) -> str:
    # TODO: implement SEARCH_KEYWORD
    pass


def count_keyword(keyword: str) -> str:
    # TODO: implement COUNT_KEYWORD
    pass