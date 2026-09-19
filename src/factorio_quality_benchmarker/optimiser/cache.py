from collections.abc import Callable


def get_from_cache[K, V](
    cache: dict[K, V],
    key: K,
    calculate: Callable[[], V],
) -> V:
    if key not in cache:
        cache[key] = calculate()

    return cache[key]
