NAME := recoll-modern-ui
IMAGE := tenasi/$(NAME)
VERSION := 0.3.0
BUILD_PATH := ./build
CONTAINER_NAME := recoll
PORT := 8080
DOCKER ?= podman

.PHONY: build run test stop release clean

build:
	$(DOCKER) build \
		--build-arg APP_VERSION=$(VERSION) \
		--build-arg CACHEBUST=$$(date +%s%N) \
		--platform linux/amd64 \
		--tag $(IMAGE):$(VERSION) \
		.
	$(DOCKER) tag $(IMAGE):$(VERSION) $(IMAGE):latest

run:
	@echo "Starting container $(CONTAINER_NAME)..."
	$(DOCKER) rm -f $(CONTAINER_NAME) 2>/dev/null || true
	$(DOCKER) run -d \
		--name $(CONTAINER_NAME) \
		--restart unless-stopped \
		-p $(PORT):8080 \
		-v "$(CURDIR)/test/data:/data:ro" \
		-v "$(CURDIR)/test/config:/root/.recoll" \
		-e RECOLL_CONFDIR=/root/.recoll \
		-e RECOLL_LOGLEVEL=INFO \
		$(IMAGE):$(VERSION)
	@echo "Container $(CONTAINER_NAME) started on http://localhost:$(PORT)"

test:
	@echo "Running tests against container $(CONTAINER_NAME)..."
	@if ! $(DOCKER) ps --filter "name=$(CONTAINER_NAME)" --filter "status=running" --format "{{.Names}}" | grep -q "^$(CONTAINER_NAME)$$"; then \
		echo "Error: Container $(CONTAINER_NAME) is not running. Start it with 'make run' first." >&2; \
		exit 1; \
	fi
	@echo "[1/4] Waiting for Web UI readiness..."
	@for i in $$(seq 1 30); do \
		if curl -s -f http://127.0.0.1:$(PORT)/ >/dev/null 2>&1; then \
			echo "      Web UI is responding (attempt $$i)"; \
			break; \
		fi; \
		if [ $$i -eq 30 ]; then \
			echo "Error: Web UI failed to respond within 30 seconds." >&2; \
			exit 1; \
		fi; \
		sleep 1; \
	done
	@echo "[2/4] Testing HTML UI root endpoint..."
	@curl -s -f http://127.0.0.1:$(PORT)/ | grep -q "Recoll" || { echo "Error: Root endpoint response did not contain expected content." >&2; exit 1; }
	@echo "      Root endpoint OK (contains Recoll UI)"
	@echo "[3/4] Testing Static Assets delivery..."
	@curl -s -f http://127.0.0.1:$(PORT)/static/style.css >/dev/null || { echo "Error: Failed to fetch static CSS." >&2; exit 1; }
	@echo "      Static assets OK"
	@echo "[4/4] Testing JSON API and Search Query..."
	@curl -s -f "http://127.0.0.1:$(PORT)/json?query=000" | grep -q '"results"' || { echo "Error: JSON API query failed." >&2; exit 1; }
	@echo "      JSON search endpoint OK"
	@echo "[5/5] Testing Advanced Search, Form Builder, and JSON Persistence..."
	@$(DOCKER) exec -i -e RECOLL_TEST_URL=http://127.0.0.1:$(PORT) $(CONTAINER_NAME) python3 - < test/test_advanced_search.py
	@echo "All tests passed successfully!"

stop:
	@echo "Stopping container $(CONTAINER_NAME)..."
	$(DOCKER) stop $(CONTAINER_NAME) 2>/dev/null || true
	$(DOCKER) rm $(CONTAINER_NAME) 2>/dev/null || true
	@echo "Container $(CONTAINER_NAME) stopped and removed."

release: build
	@HASH=$$($(DOCKER) inspect --format='{{.Id}}' "$(IMAGE):$(VERSION)" | sed 's/sha256://'); \
	$(DOCKER) save -o $(BUILD_PATH)/$(NAME)-$${HASH}.tar $(IMAGE):$(VERSION)

clean: stop
	$(DOCKER) manifest rm $(IMAGE):$(VERSION) $(IMAGE):latest 2>/dev/null || true
	$(DOCKER) image rm $(IMAGE):$(VERSION) $(IMAGE):latest 2>/dev/null || true
