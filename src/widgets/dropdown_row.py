# Imports
from gi.repository import GLib, Gtk, Adw, GObject

# Internal imports
from .base_row import BaseRow


class DropDownRow(Adw.ComboRow):
  __gtype_name__ = 'DropDownRow'

  key = GObject.Property(type=str)
  value = GObject.Property(type=int)

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    GLib.idle_add(self._post_init)

  def _post_init(self):
    flags = (
      GObject.BindingFlags.BIDIRECTIONAL
      | GObject.BindingFlags.SYNC_CREATE
    )
    self.bind_property('selected', self, 'value', flags)

  def get_key(self) -> str:
    return self.key

  def set_key(self, key: str):
    self.key = key

  def get_value(self) -> int:
    return self.value

  def set_value(self, value: int):
    self.value = value
