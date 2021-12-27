import cocotb
from cocotb.queue import Queue

from typing import Awaitable, TypeVar, Callable, Generic

V = TypeVar('V')
O = TypeVar('O')

class ProducerMonitor(Generic[V, O]):
  """
  Reusable monitor of one-way streaming data interface when an awaiter value changes.

  Generics
    V: type of value to stream
    O: type of object to monitor
  Args
    signal: named handle to be sampled when data changes
    value_resolver: function accepting handle of monitored value, returning value to place in monitor queue
    awaiter: async function defining wait criteria before fetching value and queueing
  """

  def __init__(self, signal: O, value_resolver: Callable[[O], V], awaiter: Awaitable[O]):
    self.values = Queue[V]()
    self._signal = signal
    self._coro = None
    self._value_resolver = value_resolver
    self._awaiter = awaiter

  def start(self) -> None:
    """Start monitor"""
    if self._coro is not None:
      raise RuntimeError("Monitor already started")
    self._coro = cocotb.start_soon(self._run())

  def stop(self) -> None:
    """Stop monitor"""
    if self._coro is None:
      raise RuntimeError("Monitor never started")
    self._coro.kill()
    self._coro = None

  async def _run(self) -> None:
    while True:
      await self._awaiter(self._signal)
      self.values.put_nowait(self._value_resolver(self._signal))

class ConsumerMonitor(Generic[V, O]):
  """
  Reusable monitor of one-way streaming data interface when a queue value become available.

  Generics
    V: type of value to get from queue
    O: target object to set newly arrived values
  Args
    target: object to be set when queued value received
    setter: function accepting target and new value from queue to set
    queue: queue to await values
  """

  def __init__(self, target: O, setter: Callable[[O, V], None], queue: Queue[V]):
    self._coro = None
    self._setter = setter
    self._queue = queue
    self._target = target

  def start(self) -> None:
    """Start monitor"""
    if self._coro is not None:
      raise RuntimeError("Monitor already started")
    self._coro = cocotb.start_soon(self._run())

  def stop(self) -> None:
    """Stop monitor"""
    if self._coro is None:
      raise RuntimeError("Monitor never started")
    self._coro.kill()
    self._coro = None

  async def _run(self) -> None:
    while True:
      value = await self._queue.get()
      self._setter(self._target, value)
