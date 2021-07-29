import threading
from typing import Optional, Dict, Tuple, List
from multiprocessing import connection


#from plover.oslayer.controller import Controller  # type: ignore
from plover_auto_identifier.controller import Controller  # type: ignore
# https://plover.readthedocs.io/en/latest/api/oslayer_controller.html
# https://plover2.readthedocs.io/en/latest/api/oslayer_controller.html


import gi  # type: ignore
gi.require_version('IBus', '1.0')
from gi.repository import IBus	   # type: ignore


# NOTE assuming common configuration. Not always correct.
modifiers: Dict[str, IBus.ModifierType]={
"shift_l": IBus.ModifierType.SHIFT_MASK,
"shift_r": IBus.ModifierType.SHIFT_MASK,
"control_l": IBus.ModifierType.CONTROL_MASK,
"control_r": IBus.ModifierType.CONTROL_MASK,
"alt_l": IBus.ModifierType.MOD1_MASK,
"alt_r": IBus.ModifierType.MOD1_MASK,
"meta_l": IBus.ModifierType.MOD1_MASK | IBus.ModifierType.META_MASK,
"meta_r": IBus.ModifierType.MOD1_MASK | IBus.ModifierType.META_MASK,
#IBus.ModifierType.MOD2_MASK  # numlock
#IBus.ModifierType.MOD3_MASK
"super_l": IBus.ModifierType.MOD4_MASK | IBus.ModifierType.SUPER_MASK,
"super_r": IBus.ModifierType.MOD4_MASK | IBus.ModifierType.SUPER_MASK,
"hyper_l": IBus.ModifierType.MOD4_MASK | IBus.ModifierType.HYPER_MASK,
"hyper_r": IBus.ModifierType.MOD4_MASK | IBus.ModifierType.HYPER_MASK,
"iso_level3_shift": IBus.ModifierType.MOD5_MASK,
"mode_switch": IBus.ModifierType.MOD5_MASK,
		}

keys: Dict[str, Tuple[
	int, # IBus key code
	int  # IBus modifiers that it activates
	]]={
		name: (getattr(IBus, p), modifiers.get(name, 0))
		for p in dir(IBus)
		if p.startswith("KEY_")
		for name in [p.removeprefix("KEY_").lower()]
		}

assert not (set(modifiers)-set(keys)), (set(modifiers)-set(keys))

from plover.key_combo import add_modifiers_aliases, parse_key_combo  # type: ignore
add_modifiers_aliases(keys)

from multiprocessing import connection

from pathlib import Path
import tempfile
response_path=Path(tempfile.gettempdir())/".ibus-response"


def create_response_listener()->connection.Listener:
	try:
		response_path.unlink()
	except FileNotFoundError:
		pass
	return connection.Listener(
			str(response_path),
			"AF_UNIX",
			authkey=None
			)


class KeyboardEmulation:
	def __init__(self, old_keyboard_emulation)->None:
		self._control=Controller(".ibus-listen")
		self._old_keyboard_emulation=old_keyboard_emulation

	def _send_message(self, message)->None:
		"""
		Send a message and wait for a response.

		Might freeze if the other side behave weirdly.
		"""
		listener=create_response_listener()
		self._control._send_message(message)
		listener.accept()

	def send_backspaces(self, b: int)->None:
		self._send_message(("d", b))
		#assert self._client
		#self._client.send(("d", b))

	def ibus_send_string(self, s: str)->None:
		"""
		Send a string with IBus commit_text function, and forward_key_event for some special keys.
		"""
		self._send_message(("s", s))

	def ibus_send_string_raw(self, s: str)->None:
		"""
		Send a string with IBus commit_text function.

		Might not handle some special characters (tab, newline) well. Use send_string instead.
		"""
		self._send_message(("S", s))

	def send_string(self, s: str)->None:
		return self.ibus_send_string(s)
		import re

		for part in re.split(r"([\t\n])", s):
			if not part: continue
			if part=="\t":
				self.send_key_combination("Tab")
			elif part=="\n":
				self.send_key_combination("Return")
			else:
				self.ibus_send_string(part)
		#assert self._client
		#self._client.send(s)
		#engine.instance()._commit_string(s)

	def send_key_combination(self, combo_string: str)->None:
		#self._old_keyboard_emulation.send_key_combination(combo_string)
		self.ibus_send_key_combination(combo_string)

	def ibus_send_key_combination(self, combo_string: str)->None:
		"""
		Send a keyboard combination with IBus forward_key_event function.

		Some applications are not compatible with this.

		Parameters:
			combo_string: Same format as Plover's combo_string.
		"""
		mods: IBus.ModifierType=IBus.ModifierType(0)
		result: List[Tuple[
			int, # key
			int # modifier (mask)
			]]=[]
		for (keycode, mod), is_press in parse_key_combo(combo_string, keys.get):
			result.append((keycode, int(mods if is_press else mods|IBus.ModifierType.RELEASE_MASK)))

			if is_press:
				assert not (mod&mods)
				mods|=mod
			if not is_press:
				assert (mod&mods)==mod
				mods&=~mod

		assert mods==0
		self._send_message(("c", result))

	def set_time_between_key_presses(self, ms: int)->None:
		# https://github.com/openstenoproject/plover/pull/1132
		if ms!=0:
			raise RuntimeError("Time between key presses not supported!")


class Main:
	def __init__(self, engine)->None:
		self._engine=engine
		#self._client: Optional[connection.Connection]=None
		self._old_keyboard_emulation=None

	def start(self)->None:
		#from . import main, engine

		#try:
		#	main.locale.setlocale(main.locale.LC_ALL, "")
		#except:
		#	pass

		#main.IBus.init()
		#self._app=main.IMApp(exec_by_ibus=False)
		#self._thread=threading.Thread(target=self._app.run)
		#self._thread.start()

		#from pathlib import Path
		#import tempfile
		#path=str(Path(tempfile.gettempdir())/".ibus-listen")

		#assert self._client is None
		assert self._old_keyboard_emulation is None
		#self._client=connection.Client(
		#		path,
		#		"AF_UNIX",
		#		authkey=None
		#		)

		self._old_keyboard_emulation=self._engine._keyboard_emulation
		self._engine._keyboard_emulation=KeyboardEmulation(self._old_keyboard_emulation)


	def stop(self)->None:
		assert self._old_keyboard_emulation
		self._engine._keyboard_emulation=self._old_keyboard_emulation
		self._old_keyboard_emulation=None
		#self._client.close()
		#self._client=None

		#try:
		#	self._app.stop()
		#	print("joining")
		#	self._thread.join()
		#except:
		#	import traceback
		#	traceback.print_exc()
