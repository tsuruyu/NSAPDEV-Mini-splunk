import MOD_STORE as store


def ingest(file_data: str) -> str:
    lines   = file_data.splitlines()
    parsed  = [store.parse_syslog_line(l) for l in lines]
    entries = [e for e in parsed if e is not None]

    store.write_lock.acquire()
    try:
        store.log_store.extend(entries)
    finally:
        store.write_lock.release()

    return f"SUCCESS: File received and {len(entries):,} syslog entries parsed and indexed."