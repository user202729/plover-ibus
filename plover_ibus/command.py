from . import KeyboardEmulation

def keyboard_emulation(engine)->KeyboardEmulation:
	result=engine._keyboard_emulation
	if not isinstance(result, KeyboardEmulation):
		raise RuntimeError("The plugin is not enabled")
	return result

def ibus_send_string(engine, arguments: str)->None:
	keyboard_emulation(engine).ibus_send_string(arguments)

def ibus_send_key_combination(engine, arguments: str)->None:
	keyboard_emulation(engine).ibus_send_key_combination(arguments)
