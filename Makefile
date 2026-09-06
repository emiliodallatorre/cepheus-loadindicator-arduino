-include .env

TARGET_HOST ?= arduino@$(or $(ARDUINO_HOST),juno)
PROJECT_NAME ?= $(notdir $(CURDIR))
REMOTE_DIR = ~/ArduinoApps/$(PROJECT_NAME)

.PHONY: sync start deploy stop logs logs-follow status restart

sync:
	ssh $(TARGET_HOST) "mkdir -p $(REMOTE_DIR)"
	scp -r app.yaml python sketch $(TARGET_HOST):$(REMOTE_DIR)/

start:
	ssh $(TARGET_HOST) "arduino-app-cli app start $(REMOTE_DIR) && sleep 1 && arduino-app-cli app logs $(REMOTE_DIR)"

stop:
	-ssh $(TARGET_HOST) "arduino-app-cli app stop $(REMOTE_DIR) || true"

restart: stop start

status:
	ssh $(TARGET_HOST) "arduino-app-cli app list"

logs:
	ssh $(TARGET_HOST) "arduino-app-cli app logs $(REMOTE_DIR)"

logs-follow:
	ssh -t $(TARGET_HOST) "arduino-app-cli app logs -f $(REMOTE_DIR)"

deploy: stop sync start

.PHONY: client-build client-run client-stop client-logs

client-build:
	docker compose build monitor

client-run:
	docker compose up -d monitor

client-stop:
	docker compose down

client-logs:
	docker compose logs -f monitor

