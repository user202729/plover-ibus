
import gi  # type: ignore
gi.require_version('IBus', '1.0')
from gi.repository import IBus	   # type: ignore


import typing
from typing import Dict, Tuple


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

name_to_keysym_mods: Dict[str, Tuple[
	int, # IBus keysym
	int  # IBus modifiers that it activates
	]]={
		name: (getattr(IBus, p), modifiers.get(name, 0))
		for p in dir(IBus)
		if p.startswith("KEY_")  # IBus.KEY_<name>
		for name in [p.removeprefix("KEY_").lower()]
		}

keysym_to_name: Dict[int, str]={keysym: name for name, (keysym, mods) in name_to_keysym_mods.items()}

assert not (set(modifiers)-set(name_to_keysym_mods)), (set(modifiers)-set(name_to_keysym_mods))
# !! may want to call add_modifiers_aliases(name_to_keysym_mods) later


keycode_to_keysym: typing.List[int]=[
		keymap.lookup_keysym(keycode=keycode, state=0)
		for keymap in [IBus.Keymap("us")]
		for keycode in range(256)
		]

# assuming us keyboard layout (???)
# (keycode = scancode != keyval = keysym)
keysym_to_keycode: typing.Dict[int, int]={keysym: keycode for keycode, keysym in enumerate(keycode_to_keysym)}

