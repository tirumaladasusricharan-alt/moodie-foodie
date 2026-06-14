# Use Python 3.10
FROM python:3.10

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port Flask runs on
EXPOSE 7860

# Run the application
# We use 0.0.0.0 to allow external connections from the HF proxy
# And port 7860 which is the default for Hugging Face Spaces
CMD ["python", "app.py"]
