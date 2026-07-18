"""Ring buffer tests."""

from my_network_monitor.utils.ring_buffer import RingBuffer


def test_ring_buffer_respects_maxlen() -> None:
    buffer: RingBuffer[int] = RingBuffer(maxlen=3)
    buffer.extend([1, 2, 3, 4, 5])
    assert len(buffer) == 3
    assert buffer.to_list() == [3, 4, 5]


def test_ring_buffer_clear() -> None:
    buffer: RingBuffer[int] = RingBuffer(maxlen=5)
    buffer.extend([1, 2, 3])
    buffer.clear()
    assert len(buffer) == 0


def test_ring_buffer_indexing() -> None:
    buffer: RingBuffer[str] = RingBuffer(maxlen=2)
    buffer.append("a")
    buffer.append("b")
    assert buffer[0] == "a"
    assert buffer[-1] == "b"
