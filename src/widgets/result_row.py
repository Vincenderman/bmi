# Imports
from gi.repository import GLib, GObject, Gtk, Adw

# Internal imports
from .shared import *

class ResultRow(Adw.ActionRow):
  __gtype_name__ = 'ResultRow'

  __gsignals__ = {
    'info-clicked': (GObject.SignalFlags.RUN_LAST, None, (Gtk.Widget,))
  }

  digits = GObject.Property(type=int, default=2)
  value = GObject.Property(type=float, default=0.0)
  value_label = GObject.Property(type=str, default='0.0')

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    # Setting up self
    self.set_size_request(300, 60)
    self.set_activatable(True)
    self.set_css_classes(['heading'])
    # Creating the value label
    self._value_label = Gtk.Label(
      valign=Gtk.Align.CENTER,
      css_classes=['title-3'],
    )
    self.add_suffix(self._value_label)
    # Creating the info button
    self.info_button = Gtk.Button(
      valign=Gtk.Align.CENTER,
      css_classes=['circular', 'flag'],
      icon_name='help-about-symbolic',
    )
    self.info_button.connect('clicked', self.on_info_button)
    GLib.idle_add(self._post_init)

  def _post_init(self):
    flags = (
      GObject.BindingFlags.BIDIRECTIONAL
      | GObject.BindingFlags.SYNC_CREATE
    )
    self._value_label.set_property('label', self.value_label)
    self.bind_property('value-label', self._value_label, 'label', flags)
    self.connect('notify::value', self._on_value_changed)
    self._on_value_changed()

  def set_digits(self, digits: int):
    self.digits = digits

  def get_digits(self) -> int:
    return self.digits

  def _on_value_changed(self, *args):
    if self.value is None:
      label = 'N/A'
    else:
      label = str(round(self.value, self.digits))
    self.value_label = label

  def get_value(self) -> float:
    return self.value

  def set_value(self, value: float):
    self.value = value

  def get_value_label(self) -> str:
    return self.value_label

  def set_value_label(self, label: str):
    self.value_label = label

  def on_info_button(self, button):
    self.emit('info-clicked', button)

  def set_feedback(self, result: float, thresholds: list):
    if result is None:
      set_style(self, None)
      self.set_subtitle('')
      return
    thresholds.sort(key=lambda t: t.get('value'))
    thresholds.reverse()
    for threshold in thresholds:
      threshold_value = threshold.get('value')
      if result >= threshold_value:
        self.set_subtitle(threshold.get('text'))
        set_style(self, threshold.get('style'))
        break
