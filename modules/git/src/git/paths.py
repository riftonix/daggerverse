def changed_dir_for_file(path: str, scopes: list[str], depth: int) -> str:
    normalized_path = normalize_path(path)
    if depth <= 0:
        return "."

    scope = matching_scope(normalized_path, scopes)
    if scope:
        relative_path = normalized_path.removeprefix(f"{scope}/")
        relative_parts = relative_path.split("/")[:-1]
        if not relative_parts:
            return scope
        return "/".join([scope, *relative_parts[:depth]])

    parts = normalized_path.split("/")[:-1]
    if not parts:
        return "."
    return "/".join(parts[:depth])


def matching_scope(path: str, scopes: list[str]) -> str | None:
    matching_scopes = [scope for scope in scopes if path == scope or path.startswith(f"{scope}/")]
    if not matching_scopes:
        return None
    return max(matching_scopes, key=len)


def normalize_path(path: str) -> str:
    normalized = path.strip().strip("/")
    if normalized in ("", "."):
        return "."
    return normalized.removeprefix("./")
