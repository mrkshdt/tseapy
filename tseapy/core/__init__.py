def create_callback_url(task: str, algo: str, *args) -> str:
    params = "'"
    if args:
        params = '&'.join(f"{a}='+{a}+'" for a in args)[:-2]
    url = f"'/{task}/{algo}/compute?{params}"
    return url
