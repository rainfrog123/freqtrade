# Use an official Python runtime as a parent image
FROM python:3.11

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Run your script when the container launches
CMD [ "python", "ccxt_strategy.py" ]

# docker build -t test_ccxt_strategy .
# docker run test_ccxt_strategy
# docker run -d test_ccxt_strategy
