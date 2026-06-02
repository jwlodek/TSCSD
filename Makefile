.PHONY: all phoebus uv clean

all: uv phoebus

uv:
	curl -LsSf https://astral.sh/uv/install.sh | sh
	uv venv
	uv pip sync requirements.txt

phoebus:
	mkdir -p phoebus
	mkdir -p phoebus/jvm

	wget --no-verbose https://download.oracle.com/java/17/archive/jdk-17.0.12_linux-x64_bin.tar.gz -O ./phoebus/jdk-17.0.12_linux-x64_bin.tar.gz
	tar xfvz ./phoebus/jdk-17.0.12_linux-x64_bin.tar.gz --directory ./phoebus/jvm && mv ./phoebus/jvm/jdk-17.0.12 ./phoebus/jvm/jdk-17
	rm ./phoebus/jdk-17.0.12_linux-x64_bin.tar.gz

	wget --no-verbose https://github.com/ControlSystemStudio/phoebus/releases/download/v4.7.3/Phoebus-4.7.3-linux.tar.gz -O ./phoebus/Phoebus-4.7.3-linux.tar.gz
	tar xfvz ./phoebus/Phoebus-4.7.3-linux.tar.gz --directory ./phoebus
	mv ./phoebus/product-4.7.3/* ./phoebus
	chmod +x ./phoebus/phoebus.sh

	rm ./phoebus/Phoebus-4.7.3-linux.tar.gz
	rmdir ./phoebus/product-4.7.3

clean:
	rm -rf phoebus
	rm -rf venv
