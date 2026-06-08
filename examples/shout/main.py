import json, os
inp = json.load(open(os.environ["FN_INPUTS"]))
print("shouting:", inp["greeting"])
json.dump({"shout": inp["greeting"].upper()}, open(os.environ["FN_OUTPUTS"], "w"))
