# window.py
#
# Copyright 2024 philipp
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# SPDX-License-Identifier: GPL-2.0-or-later

# Imports
import copy
import math
import re

# Gtk imports
from gi.repository import GObject, Gtk, Adw, Gio, Gdk

# Internal imports
from . import widgets, calculate


@Gtk.Template(resource_path='/io/github/philippkosarev/bmi/window.ui')
class BmiWindow(Adw.ApplicationWindow):
  __gtype_name__ = 'BmiWindow'

  settings = GObject.Property(type=Gio.Settings)

  # Important Widgets
  toast_overlay = Gtk.Template.Child()
  clamp = Gtk.Template.Child()
  orientable_box = Gtk.Template.Child()
  simple_breakpoint = Gtk.Template.Child()
  advanced_breakpoint = Gtk.Template.Child()
  advanced_inputs_clamp = Gtk.Template.Child()

  # Input rows
  height_input_row = Gtk.Template.Child()
  weight_input_row = Gtk.Template.Child()
  gender_input_row = Gtk.Template.Child()
  age_input_row = Gtk.Template.Child()
  waist_input_row = Gtk.Template.Child()
  hip_input_row = Gtk.Template.Child()

  # Result rows
  bmi_result_row = Gtk.Template.Child()
  whtr_result_row = Gtk.Template.Child()
  whr_result_row = Gtk.Template.Child()
  bri_result_row = Gtk.Template.Child()

  def __init__(self, application: Gio.Application):
    # Setting up self
    super().__init__(application=application)
    self.settings = application.get_settings()
    flags = GObject.BindingFlags.BIDIRECTIONAL
    self.bind_property('settings', application, 'settings', flags)

    # Configuring inputs
    self.input_rows = [
      self.height_input_row,
      self.weight_input_row,
      self.gender_input_row,
      self.age_input_row,
      self.waist_input_row,
      self.hip_input_row,
    ]
    for row in self.input_rows:
      key = row.get_key()
      row.set_value(self.settings[key])
      row.connect('notify::value', self.update_results)

    # Configuring results
    self.result_rows = [
      self.bmi_result_row,
      self.whtr_result_row,
      self.whr_result_row,
      self.bri_result_row,
    ]
    for row in self.result_rows:
      row.connect('activated', self.copy_result)
      row.connect('info-clicked', self.on_result_row_info_clicked)

    self.result_row_info = {
      self.bmi_result_row: {
        'calc-function': calculate.bmi,
        'context': {
          'calc-function': calculate.mass_from_bmi_and_height,
          'description': _("With the same height, this is what weight you need to get different BMI thresholds"),
        },
        'thresholds': [
          {'text': _('Underweight [Severe]'),   'value': 0,    'style': 0},
          {'text': _('Underweight [Moderate]'), 'value': 16,   'style': 0},
          {'text': _('Underweight [Mild]'),     'value': 17,   'style': 0},
          {'text': _('Healthy'),                'value': 18.5, 'style': 1},
          {'text': _('Overweight'),             'value': 25,   'style': 2},
          {'text': _('Obese [Class 1]'),        'value': 30,   'style': 3},
          {'text': _('Obese [Class 2]'),        'value': 35,   'style': 3},
          {'text': _('Obese [Class 3]'),        'value': 40,   'style': 3},
        ],
      },
      self.whtr_result_row: {
        'calc-function': calculate.whtr,
        'thresholds': [
          {'text': _('Healthy'),   'value': 0,                        'style': 1},
          {'text': _('Unhealthy'), 'value': calculate.whtr_unhealthy, 'style': 2},
        ],
      },
      self.whr_result_row: {
        'calc-function': calculate.whr,
        'thresholds': [
          {'text': _('Healthy'),    'value': 0,                        'style': 1},
          {'text': _('Overweight'), 'value': calculate.whr_overweight, 'style': 2},
          {'text': _('Obese'),      'value': calculate.whr_obese,      'style': 3},
        ],
      },
      self.bri_result_row: {
        'calc-function': calculate.bri,
        'thresholds': [
          {'text': _('Very lean'),     'value': 0,    'style': 0},
          {'text': _('Lean'),          'value': 3.41, 'style': 1},
          {'text': _('Average'),       'value': 4.45, 'style': 1},
          {'text': _('Above average'), 'value': 5.46, 'style': 2},
          {'text': _('High'),          'value': 6.91, 'style': 3},
        ],
      },
    }

    # Setting stuff from settings
    window_width, window_height = self.settings['window-size']
    self.set_default_size(window_width, window_height)
    self.set_advanced_mode(self.settings['advanced-mode'])
    self.set_imperial(self.settings['measurement-system'])
    self.update_results()

    # Connecting stuff
    self.settings.connect('changed', self._on_settings_value_changed)
    self.simple_breakpoint.connect('apply', self.on_simple_breakpoint_apply)
    self.simple_breakpoint.connect('unapply', self.on_simple_breakpoint_unapply)
    self.advanced_breakpoint.connect('apply', self.on_advanced_breakpoint_apply)
    self.advanced_breakpoint.connect('unapply', self.on_advanced_breakpoint_unapply)
    self.connect("close-request", self.on_close_request)

  def get_settings(self) -> Gio.Settings:
    return self.settings

  def set_settings(self, settings: Gio.Settings):
    self.settings = settings

  def set_advanced_mode(self, mode: bool):
    self.advanced_inputs_clamp.set_visible(mode)
    self.whtr_result_row.set_visible(mode)
    self.whr_result_row.set_visible(mode)
    self.bri_result_row.set_visible(mode)
    self.update_breakpoints()

  def get_inputs(self):
    inputs = {}
    for row in self.input_rows:
      if hasattr(row, 'get_centimetres'):
        value = row.get_centimetres()
      elif hasattr(row, 'get_kilograms'):
        value = row.get_kilograms()
      else:
        value = row.get_value()
      key = row.get_key()
      inputs[key] = value
      if self.settings['remember-inputs']:
        self.settings[key] = value
      else:
        self.settings.reset(key)
    return inputs

  def calc_row_values(self, row: widgets.ResultRow, inputs: dict) -> tuple:
    info = self.result_row_info.get(row)
    calc_function = info.get('calc-function')
    result = calc_function(**inputs)
    thresholds = copy.deepcopy(info.get('thresholds'))
    for i in range(len(thresholds)):
      threshold_value = thresholds[i]['value']
      if callable(threshold_value):
        thresholds[i]['value'] = threshold_value(**inputs)
    return result, thresholds

  def update_results(self, *args):
    inputs = self.get_inputs()
    for row in self.result_row_info:
      result, thresholds = self.calc_row_values(row, inputs)
      row.set_value(result)
      row.set_feedback(result, thresholds)

  def on_result_row_info_clicked(self, row: widgets.ResultRow, button: Gtk.Button):
    dialog = widgets.ResultDialog(row)
    inputs = self.get_inputs()
    result, thresholds = self.calc_row_values(row, inputs)
    dialog.set_result(result)
    dialog.set_feedback(result, thresholds)
    if 'context' in self.result_row_info.get(row):
      description, thresholds = self.get_row_context(row)
      dialog.set_context(description, thresholds, bool(self.settings['measurement-system']))
    dialog.present(self)

  def get_row_context(self, row: widgets.ResultRow) -> tuple:
    info = self.result_row_info.get(row)
    thresholds = copy.deepcopy(info.get('thresholds'))
    context_info = info.get('context')
    description = context_info.get('description')
    calc_function = context_info.get('calc-function')
    inputs = self.get_inputs()
    for i in range(len(thresholds)):
      threshold_value = thresholds[i]['value']
      value = calc_function(threshold_value, **inputs)
      thresholds[i]['value'] = value
    return description, thresholds

  def copy_result(self, row: widgets.ResultRow):
    clipboard = Gdk.Display.get_default().get_clipboard()
    clipboard.set(row.value_label)
    self.show_toast(_("Result copied"))

  def show_toast(self, text):
    self.toast_overlay.dismiss_all()
    toast = Adw.Toast(title=text, timeout=1)
    self.toast_overlay.add_toast(toast)

  def set_imperial(self, measurement_system: int):
    imperial = bool(measurement_system)
    for row in self.input_rows:
      if hasattr(row, 'imperial'):
        row.set_imperial(imperial)

  def _on_settings_value_changed(self, settings: Gio.Settings, key: str):
    update_functions = {
      'advanced-mode': self.set_advanced_mode,
      'measurement-system': self.set_imperial,
      'remember-inputs': self.update_results,
    }
    update_function = update_functions.get(key)
    if not update_function:
      return
    update_function(settings[key])

  def _eval_breakpoint(self, adw_breakpoint):
    width = self.get_size(Gtk.Orientation.HORIZONTAL)
    height = self.get_size(Gtk.Orientation.VERTICAL)
    condition = adw_breakpoint.get_condition().to_string()
    condition = condition.replace('min-width:', 'width >')
    condition = condition.replace('max-width:', 'width <')
    condition = condition.replace('min-height:', 'height >')
    condition = condition.replace('max-height:', 'height <')
    condition = condition.split('and')
    for statement in condition:
      combined = re.search('([0-9]).*', statement).group().strip()
      units = combined[-2] + combined[-1] # Last 2 chars (i.e. px, sp or pt)
      value = float(combined.removesuffix(units))
      adw_lenght_units = {u.name.lower(): u for u in Adw.LengthUnit}
      units = adw_lenght_units[units]
      pixels = math.ceil( Adw.LengthUnit.to_px(units, value) )
      statement = statement.replace(combined, str(pixels))
      if not eval(statement):
        return False
    return True

  def on_simple_breakpoint_apply(self, adw_breakpoint = None):
    if self.settings['advanced-mode']:
      return
    self.set_ui_orientation(Gtk.Orientation.HORIZONTAL)

  def on_simple_breakpoint_unapply(self, adw_breakpoint = None):
    if self.settings['advanced-mode']:
      return
    self.set_ui_orientation(Gtk.Orientation.VERTICAL)

  def on_advanced_breakpoint_apply(self, adw_breakpoint = None):
    self.set_ui_orientation(Gtk.Orientation.HORIZONTAL)

  def on_advanced_breakpoint_unapply(self, adw_breakpoint = None):
    self.set_ui_orientation(Gtk.Orientation.VERTICAL)

  def set_ui_orientation(self, orientation: Gtk.Orientation):
    self.orientable_box.set_orientation(orientation)
    if orientation is Gtk.Orientation.HORIZONTAL:
      self.orientable_box.set_spacing(24);
    else:
      self.orientable_box.set_spacing(16);

  def update_breakpoints(self):
    if self._eval_breakpoint(self.advanced_breakpoint):
      self.on_advanced_breakpoint_apply()
    else:
      self.on_advanced_breakpoint_unapply()
    if self._eval_breakpoint(self.simple_breakpoint):
      self.on_simple_breakpoint_apply()
    else:
      self.on_simple_breakpoint_unapply()

  def on_close_request(self, *args):
    """Action after closing the app window."""
    width = self.get_size(Gtk.Orientation.HORIZONTAL)
    height = self.get_size(Gtk.Orientation.VERTICAL)
    self.settings['window-size'] = (width, height)
