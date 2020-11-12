CURRENT_DIR := $(shell pwd)

JUPYTER_ASCENDING_PYCHARM_VERSION := 1.0
PYCHARM_VERSION := 2019.3

install_dev:
	poetry install
	jupyter nbextension install --py --symlink --sys-prefix jupyter_ascending
	jupyter nbextension enable jupyter_ascending --py --sys-prefix
	jupyter serverextension enable jupyter_ascending --sys-prefix --py

pycharm_install:
	echo "This probably will not work for you."
	echo "Ask TJ how to install the plugin..."
	echo ""
	mkdir -p ~/$(PYCHARM_VERSION)/config/plugins/jupyter_ascending/lib/
	ls -s $(CURRENT_DIR) ./plugins/pycharm/build/idea-sandbox/plugins/jupyter_ascending/lib/jupyter_ascending-$(JUPYTER_ASCENDING_PYCHARM_VERSION)-SNAPSHOT.jar ~/$(PYCHARM_VERSION)/ ~/.PyCharm2019.3/config/plugins/jupyter_ascending/lib/jupyter_ascending-1.0-SNAPSHOT.jar

# test:
# 	pytest tests/
