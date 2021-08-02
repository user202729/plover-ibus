import threading
from typing import Optional, Dict, Tuple, List
from multiprocessing import connection


#from plover.oslayer.controller import Controller  # type: ignore
from plover_auto_identifier.controller import Controller  # type: ignore
# https://plover.readthedocs.io/en/latest/api/oslayer_controller.html
# https://plover2.readthedocs.io/en/latest/api/oslayer_controller.html





from plover.key_combo import add_modifiers_aliases, parse_key_combo  # type: ignore
from .ibus_lib import name_to_keysym_mods
name_to_keysym_mods=dict(name_to_keysym_mods)
add_modifiers_aliases(name_to_keysym_mods)

from multiprocessing import connection

from . import lib
from .lib import response_path, listen_path_name
from .ibus_lib import IBus


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
		self._control=Controller(listen_path_name)
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
		self._send_message((lib.BACKSPACE, b))
		#assert self._client
		#self._client.send(("d", b))

	def ibus_send_string(self, s: str)->None:
		"""
		Send a string with IBus commit_text function, and forward_key_event for some special name_to_keysym_mods.
		"""
		self._send_message((lib.SMART_STRING, s))

	def ibus_send_string_raw(self, s: str)->None:
		"""
		Send a string with IBus commit_text function.

		Might not handle some special characters (tab, newline) well. Use send_string instead.
		"""
		self._send_message((lib.RAW_STRING, s))

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
		for (keycode, mod), is_press in parse_key_combo(combo_string, name_to_keysym_mods.get):
			result.append((keycode, int(mods if is_press else mods|IBus.ModifierType.RELEASE_MASK)))

			if is_press:
				assert not (mod&mods)
				mods|=mod
			if not is_press:
				assert (mod&mods)==mod
				mods&=~mod

		assert mods==0
		self._send_message((lib.COMBINATION, result))

	def send_key_combination(self, combo_string: str)->None:
		self._old_keyboard_emulation.send_key_combination(combo_string)
		#self.ibus_send_key_combination(combo_string)

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
