import json
import requests
import time
import validators

def current_time_ms() -> int:
    return round(time.time() * 1000)

def get_input_url() -> str:
	gta5_nativedb_link = "https://raw.githubusercontent.com/alloc8or/gta5-nativedb-data/master/natives.json"
	rdr3_nativedb_link = "https://raw.githubusercontent.com/alloc8or/rdr3-nativedb-data/master/natives.json"

	print(f"Input:")
	print(f"  1: GTA5 NativeDB Data ({gta5_nativedb_link})")
	print(f"  2: RDR3 NativeDB Data ({rdr3_nativedb_link})")
	print(f"  3: Custom")
	input_url_n = -1
	while input_url_n < 1 or input_url_n > 3:
		try:
			int_in = int(input("> "))
			input_url_n = int_in
		except:
			continue
	if input_url_n == 1:
		return gta5_nativedb_link
	elif input_url_n == 2:
		return rdr3_nativedb_link
	elif input_url_n == 3:
		print("Custom URL:")
		custom_url_out = "!" # intentionally invalid by default
		while not validators.url(custom_url_out):
			custom_url_out = input("> ")
		return custom_url_out
	
	print("impossible.")
	raise Exception("this is foul play.")

def fix_native_name(name: str) -> str:
	if name.startswith("_0x"): # unknown and has no name, don't do anything with it
		return name
	
	# if you're confused, you'll see why this '_' is added very soon
	name_out = "_" + name.lower()
	letters = "abcdefghijklmnopqrstuvwxyz"
	capital_letters = letters.upper()

	cur_letter_idx = 0
	for letter in letters:
		name_out = name_out.replace(f"_{letter}", f"{capital_letters[cur_letter_idx]}")
		cur_letter_idx += 1
	
	return name_out # kachow

file_content_out = """#ifndef NATIVE_DECL
#	if defined(_MSC_VER)
#		define NATIVE_DECL __forceinline
#	elif defined(__clang__) || defined(__GNUC__)
#		define NATIVE_DECL __attribute__((always_inline)) inline
#	else
#		define NATIVE_DECL inline
#	endif
#endif

namespace Commands {
"""

# get our json data
content_url = get_input_url()
start_req_time = current_time_ms()
nativedb_req = requests.get(content_url)
nativedb_json = json.loads(nativedb_req.text)
nativedb_req.close()
print(f"Obtained native database in {current_time_ms() - start_req_time}ms.")

# cool we have our json data time to write
start_gen_time = current_time_ms()
current_namespace_idx = 0
for namespace, functions in nativedb_json.items():
	current_namespace_idx += 1
	is_last_namespace = len(nativedb_json.items()) == current_namespace_idx
	file_content_out += f"\tnamespace {namespace} {{\n"
	for native_hash, native_data in functions.items():
		has_varargs = False

		native_return_type = native_data["return_type"]
		native_name = fix_native_name(native_data["name"])

		# hey if it works, it works
		native_params_raw = native_data["params"]
		native_params_input_data = []
		native_params_input = ""
		native_params_exec_data = []
		native_params_exec = ""

		native_return_keyword = "return "
		if native_return_type.lower().__eq__("void"):
			native_return_keyword = ""

		for param_in in native_params_raw:
			param = param_in
			if param["name"].__eq__("..."):
				param["type"] = "Args&&..."
				param["name"] = "varargs"
				native_params_exec_data.append(f"{param['name']}...")
				has_varargs = True
			else:
				native_params_exec_data.append(f"{param['name']}")
			native_params_input_data.append(f"{param['type']} {param['name']}")
		native_params_input = ", ".join(native_params_input_data)
		native_params_exec = ", ".join(native_params_exec_data)
		if len(native_params_exec) > 0:
			native_params_exec = ", " + native_params_exec

		# we do a bit of writing
		if has_varargs == True:
			file_content_out += f"\t\ttemplate <typename... Args>\n"
		file_content_out += f"\t\tNATIVE_DECL {native_return_type} {native_name}({native_params_input}) {{ {native_return_keyword}invoke<{native_return_type}>({native_hash}{native_params_exec}); }}\n"
	file_content_out += f"\t}}\n"
	if not is_last_namespace:
		file_content_out += "\n"

file_content_out += "}"
print(f"Generated natives file in {current_time_ms() - start_req_time}ms.")

print("State the filename for the natives (default, if blank, is `natives.hpp`):")
file_name = input("> ")

if len(file_name) == 0:
	file_name = "natives.hpp"

start_write_time = current_time_ms()
generated_natives_file = open(file_name, "w")
generated_natives_file.write(file_content_out)
generated_natives_file.close()
print(f"Finished writing to `{file_name}` in {current_time_ms() - start_write_time}ms.")
