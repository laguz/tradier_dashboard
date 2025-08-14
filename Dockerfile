# --- Build Stage ---
# Use a full Python image to build wheels for our dependencies
FROM python:3.8 AS builder

# Set the working directory
WORKDIR /usr/src/app

# Install build dependencies
RUN pip install --upgrade pip
RUN pip install wheel

# Copy requirements and install dependencies as wheels
# This leverages Docker's layer caching effectively
COPY ./requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /usr/src/app/wheels -r requirements.txt


# --- Final Stage ---
# Use a slim image for a smaller footprint
FROM python:3.8-slim

# Create a non-root user to run the application
RUN addgroup --system app && adduser --system --group app

# Set the working directory
WORKDIR /home/app

# Copy the pre-built wheels from the builder stage
COPY --from=builder /usr/src/app/wheels /wheels

# Install the wheels using the copied packages
# This avoids needing build tools in the final image
COPY ./requirements.txt .
RUN pip install --no-cache /wheels/*

# Copy the application source code
# Ensure the correct permissions for the non-root user
COPY --chown=app:app . .

# Switch to the non-root user
USER app

# Expose the port the app runs on
EXPOSE 5000

# Set the command to run the application
CMD ["flask", "run", "--host=0.0.0.0"]