TARGET_HOST ?= arduino@juno
PROJECT_NAME ?= $(notdir $(CURDIR))
REMOTE_DIR = ~/ArduinoApps/$(PROJECT_NAME)

.PHONY: sync start deploy stop logs restart

sync:
	ssh $(TARGET_HOST) "mkdir -p $(REMOTE_DIR)"
	scp -r app.yaml python sketch $(TARGET_HOST):$(REMOTE_DIR)/

start:
	ssh $(TARGET_HOST) "arduino-app-cli app start $(REMOTE_DIR)"

stop:
	ssh $(TARGET_HOST) "arduino-app-cli app stop $(REMOTE_DIR)"

restart: stop start

logs:
	ssh $(TARGET_HOST) "arduino-app-cli app logs $(REMOTE_DIR)"

deploy: sync start
