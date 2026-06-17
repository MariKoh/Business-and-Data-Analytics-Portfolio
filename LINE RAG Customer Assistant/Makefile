.PHONY: install index chat serve test eval docker up clean

install:        ## Install Python dependencies
	pip install -r requirements.txt

index:          ## Embed the knowledge base and upsert to Pinecone
	python -m src.ingest

chat:           ## Run the local LINE simulator (no live channel needed)
	python -m scripts.simulate_chat

serve:          ## Run the FastAPI webhook locally on :8000
	uvicorn src.app:app --reload --port 8000

test:           ## Run unit tests (skips @integration)
	pytest -m "not integration" -q

eval:           ## Run the offline RAG evaluation harness
	python -m eval.run_eval

docker:         ## Build the Docker image
	docker build -t moomhom-line-rag .

up:             ## Start the service via docker-compose
	docker compose up --build

clean:          ## Remove local caches (does NOT delete the Pinecone index)
	rm -rf __pycache__ .pytest_cache .hf_cache src/__pycache__ tests/__pycache__
