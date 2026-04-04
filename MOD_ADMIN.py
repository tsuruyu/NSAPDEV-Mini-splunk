import MOD_STORE


def purge() -> str:
    MOD_STORE.write_lock.acquire()
    try:
        count = len(MOD_STORE.log_store)
        MOD_STORE.log_store.clear()
    finally:
        MOD_STORE.write_lock.release()

    return f"SUCCESS: {count:,} indexed log entries have been erased."