def format_dict(obj: dict) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)

def format_list(string_list: list[str]) -> str:
    prefixed = ["- " + item for item in string_list]
    return "\n".join(prefixed)
