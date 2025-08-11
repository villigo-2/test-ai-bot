run:
	python -m app.main

docker-build:
	docker build -t test-ai-bot .

docker-run:
	docker run --rm --env-file .env test-ai-bot


