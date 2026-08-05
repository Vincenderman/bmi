# Imports
from gi.repository import GObject, Gtk, Adw

# Internal imports
from .spin_row import SpinRow
from .shared import *


class MassRow(SpinRow):
  __gtype_name__ = 'MassRow'

  imperial = GObject.Property(type=bool, default=False)

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.set_subtitle(_('Kilograms'))
    self.connect('notify::imperial', self._on_imperial_changed)

  def _on_imperial_changed(self, *args):
    value = self.get_value()
    if self.imperial is True:
      convert_func = kg_to_lb
      self.set_subtitle(_('Pounds'))
    else:
      convert_func = lb_to_kg
      self.set_subtitle(_('Kilograms'))
    self.value = convert_func(self.value)

  def get_imperial(self) -> bool:
    return self.imperial

  def set_imperial(self, imperial: bool):
    self.imperial = imperial

  def get_kilograms(self):
    if self.imperial:
      return lb_to_kg(self.get_value())
    else:
      return self.get_value()

  def get_pounds(self):
    if self.imperial:
      return self.get_value()
    else:
      return kg_to_lb(self.get_value())
