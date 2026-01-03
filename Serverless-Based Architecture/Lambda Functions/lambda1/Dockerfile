
FROM public.ecr.aws/lambda/python:3.11

# Install dependences
COPY requirements.txt .
RUN pip install -r requirements.txt -t /python

# Create layer structure
RUN mkdir -p /layer/python
RUN cp -r /python/* /layer/python/

CMD ["echo", "Layer built successfully"]