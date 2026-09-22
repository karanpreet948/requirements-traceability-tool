FROM python:3.11-slim

WORKDIR /app

# Install dependencies first so Docker can cache this layer independently
# of source-code changes.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY rtm/ ./rtm/
COPY data/ ./data/

# Default: build the RTM from the committed synthetic sample data.
# Override the command to point at different --requirements/--stories/--tests
# files (e.g. mounted at runtime via `docker run -v`).
ENTRYPOINT ["python", "-m", "rtm"]
CMD ["build", \
     "--requirements", "data/requirements.yaml", \
     "--stories", "data/user_stories.yaml", \
     "--tests", "data/test_cases.yaml", \
     "--output", "out/rtm.xlsx"]
