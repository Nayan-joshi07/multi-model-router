IMG=multi-model-router:local

run:            ## run locally with hot reload
	uvicorn app.main:app --reload --port 8000
test:
	pytest -q
docker-build:
	docker build -t $(IMG) .
docker-run:
	docker compose up --build
k8s-load:       ## load image into minikube (use `kind load docker-image` for kind)
	minikube image load $(IMG)
k8s-deploy:
	kubectl apply -f k8s/00-namespace.yaml -f k8s/01-configmap.yaml \
	  -f k8s/03-deployment.yaml -f k8s/04-service.yaml -f k8s/05-hpa.yaml
k8s-forward:
	kubectl -n llm-router port-forward svc/router 8080:80
k8s-clean:
	kubectl delete namespace llm-router
lambda-local:   ## run the Lambda image locally with the Runtime Interface Emulator
	docker build -f lambda/Dockerfile -t router-lambda . && docker run -p 9000:8080 router-lambda
lambda-deploy:
	cd lambda && sam build && sam deploy --guided
