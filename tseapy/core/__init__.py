def create_callback_url(task: str, algo: str, *args) -> str:
    _ = args
    return f"'/{task}/{algo}/compute'"
