run:
	python -m app.main

docker-build:
	docker build -t test-ai-bot .

docker-run:
	docker run --rm \
	  -e BOT_TOKEN=$$BOT_TOKEN \
	  -e OPENROUTER_API_KEY=$$OPENROUTER_API_KEY \
	  -e OPENROUTER_MODEL=$$OPENROUTER_MODEL \
	  test-ai-bot


