"""AWS Lambda entrypoint. Mangum translates API Gateway / Function URL
events into ASGI calls, so the exact same FastAPI app runs serverless."""
from mangum import Mangum
from app.main import app

handler = Mangum(app, lifespan="off")
