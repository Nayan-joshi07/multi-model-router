# Lambda container image (build from project root: docker build -f lambda/Dockerfile .)
FROM public.ecr.aws/lambda/python:3.12
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ${LAMBDA_TASK_ROOT}/app
COPY lambda/handler.py ${LAMBDA_TASK_ROOT}/
CMD ["handler.handler"]
