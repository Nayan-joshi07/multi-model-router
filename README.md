# Multi-Model Router (learning project)

One FastAPI service that picks the right LLM per request (OpenAI, Anthropic, Gemini, or a free
**mock** provider), falls back automatically on failure, and deploys three ways:
**Docker**, **Kubernetes**, and **AWS Lambda**. No API keys needed to start.

```
client -> /chat -> router.choose()  -> primary model
                        |  fails?
                        +-> fallback chain -> next model ... -> response (+cost, latency, attempts)
```

## Project map
| Path | What you learn |
|---|---|
| `app/providers/` | Adapter pattern: one class per vendor, same `Completion` output |
| `app/router.py` | Routing strategies (`rules`, `cheapest`, `quality`, `explicit`) + fallback |
| `app/main.py` | API: `/chat`, `/route/preview`, `/models`, `/health`, `/ready` |
| `Dockerfile` | Multi-stage build, non-root user, healthcheck |
| `k8s/` | Namespace, ConfigMap, Secret, Deployment (probes, rolling update), Service, HPA |
| `lambda/` | Mangum adapter, Lambda container image, SAM template with Function URL |

## Stage 1 - Run locally (15 min)
```bash
pip install -r requirements.txt -r requirements-dev.txt
make test
make run                                   # http://localhost:8000/docs
curl -s localhost:8000/chat -H 'content-type: application/json' -d '{"prompt":"hi"}'
curl -s localhost:8000/chat -H 'content-type: application/json' -d '{"prompt":"explain why X fails"}'
curl -s localhost:8000/route/preview -H 'content-type: application/json' -d '{"prompt":"hi","strategy":"quality"}'
```
**Try:** `MOCK_FAIL=mock-fast make run`, send "hi", and read the `attempts` field to see fallback.
Then add a real key (`export ANTHROPIC_API_KEY=...`) and watch `/models` light up.

## Stage 2 - Docker (20 min)
```bash
cp .env.example .env
make docker-run            # docker compose up --build
```
**Learn:** why multi-stage keeps the image small (`docker images`), why `USER 10001` matters,
how `env_file` keeps secrets out of the image.

## Stage 3 - Kubernetes (45 min, use minikube or kind)
```bash
minikube start && minikube addons enable metrics-server
make docker-build && make k8s-load
kubectl -n llm-router create secret generic router-secrets --from-literal=ANTHROPIC_API_KEY=   # optional
make k8s-deploy
kubectl -n llm-router get pods -w
make k8s-forward           # then curl localhost:8080/chat ...
```
**Experiments:**
- Kill a pod: `kubectl -n llm-router delete pod -l app=router --wait=false`, watch it self-heal.
- Change `ROUTER_STRATEGY` in the ConfigMap to `cheapest`, then `kubectl -n llm-router rollout restart deploy/router`.
- Load test (`hey -z 60s -c 50 ...`) and watch `kubectl -n llm-router get hpa -w` scale up.
- Break the readiness probe path and see the pod stay out of the Service.

## Stage 4 - AWS Lambda (30 min)
```bash
make lambda-local          # Runtime Interface Emulator on :9000
# in another terminal, invoke with a Function URL style event:
curl -s localhost:9000/2015-03-31/functions/function/invocations -d '{
 "version":"2.0","rawPath":"/health","rawQueryString":"","headers":{},
 "requestContext":{"http":{"method":"GET","path":"/health","sourceIp":"1.1.1.1"}},"isBase64Encoded":false}'
make lambda-deploy         # needs AWS CLI + SAM CLI; prints a public Function URL
```
**Learn:** cold starts (first call vs next), why `Mangum` lets one codebase serve both K8s and Lambda,
and the trade-off: Lambda = zero idle cost, K8s = steady latency + full control.

## Stretch goals
1. **Semantic routing:** classify prompts with embeddings instead of regex.
2. **Caching:** add Redis (compose service + K8s StatefulSet) keyed on prompt hash.
3. **Observability:** expose Prometheus metrics (`prometheus-fastapi-instrumentator`) per model.
4. **Budget guard:** reject or downgrade when daily spend crosses a limit.
5. **Streaming:** SSE responses via `StreamingResponse`.
6. **Ingress + TLS** in K8s, **Secrets Manager** for Lambda keys, **GitHub Actions** CI to build and push.

> Model prices in `app/config.py` are illustrative; update them from each provider's pricing page.
