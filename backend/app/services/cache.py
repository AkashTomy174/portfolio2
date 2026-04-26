from collections import OrderedDict
from hashlib import sha256
from typing import Any


class LruCache:
  def __init__(self, max_items: int) -> None:
    self.max_items = max_items
    self._items: OrderedDict[str, dict[str, Any]] = OrderedDict()

  @staticmethod
  def key(message: str, voice: bool) -> str:
    normalized = " ".join(message.lower().split())
    return sha256(f"{normalized}|voice={voice}".encode("utf-8")).hexdigest()

  def get(self, key: str) -> dict[str, Any] | None:
    item = self._items.get(key)
    if item is None:
      return None
    self._items.move_to_end(key)
    return item

  def set(self, key: str, value: dict[str, Any]) -> None:
    self._items[key] = value
    self._items.move_to_end(key)
    while len(self._items) > self.max_items:
      self._items.popitem(last=False)
