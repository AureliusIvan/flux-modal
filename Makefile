.PHONY: all

all:
	modal serve comfyui-flux.py

.PHONY: clean
clean:
	modal serve comfyui-flux.py --clean