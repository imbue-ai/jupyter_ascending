from itertools import takewhile
from typing import Callable
from typing import List
from typing import Sequence


def get_matching_tail_tokens(a: Sequence, b: Sequence) -> List:
    return list(takewhile(lambda parts: parts[0] == parts[1], zip(reversed(a), reversed(b))))


# TODO: This was just as an example, idk if it works.
def compose(*args: Callable) -> Callable:
    def _func(result):
        for f in reversed(args):
            result = f(result)

        return result

    return _func
