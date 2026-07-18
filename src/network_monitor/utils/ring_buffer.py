"""Fixed-size ring buffer."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Iterator


class RingBuffer[T]:
    """Buffer that automatically drops the oldest items once maxlen is exceeded."""

    def __init__(self, maxlen: int) -> None:
        self._buffer: deque[T] = deque(maxlen=maxlen)
        self._maxlen = maxlen

    @property
    def maxlen(self) -> int:
        return self._maxlen

    def append(self, item: T) -> None:
        self._buffer.append(item)

    def extend(self, items: Iterable[T]) -> None:
        self._buffer.extend(items)

    def clear(self) -> None:
        self._buffer.clear()

    def to_list(self) -> list[T]:
        return list(self._buffer)

    def __len__(self) -> int:
        return len(self._buffer)

    def __iter__(self) -> Iterator[T]:
        return iter(self._buffer)

    def __getitem__(self, index: int) -> T:
        return self._buffer[index]
