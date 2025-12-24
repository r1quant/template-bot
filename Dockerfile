# Stage 1: Builder - Install dependencies with uv
FROM python:3.13.11-slim AS builder

# Install uv from the official image
COPY --from=ghcr.io/astral-sh/uv:0.9.18 /uv /usr/bin/uv

# Set the working directory for subsequent instructions
WORKDIR /myproject

# Copy lock file and pyproject.toml
COPY pyproject.toml uv.lock ./

# Install dependencies into a virtual environment within the builder stage
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen ;
  
# Stage 2: Runtime - Copy application code and the venv
FROM python:3.13.11-slim AS final 

# Set the working directory for subsequent instructions
WORKDIR /myproject

# Copy the virtual environment and application code from the builder stage
COPY --from=builder /myproject/.venv /myproject/.venv
COPY /data ./data
COPY /app ./app

# Add the virtual environment's bin directory to the PATH
ENV PATH="/myproject/.venv/bin:$PATH"

EXPOSE 8000

# Command to run the application using uvicorn from the venv
# Using the exec form ensures proper signal handling
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

#--------------
# Commands  
#--------------

# Build a Docker image using the file "./Dockerfile", the current directory as context, and name it "templatebot"
# > docker build -f ./Dockerfile . -t templatebot

# Run a container from "templatebot" image in interactive mode with a bash shell, and delete the container automatically when it stops
# > docker run --rm -it templatebot bash 