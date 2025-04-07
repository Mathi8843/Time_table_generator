import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import tensorflow as tf
from tensorflow.keras import layers, models
import numpy as np

# Generate some synthetic data for demonstration
np.random.seed(42)
X = np.random.rand(1000, 1)  # 1000 samples, 1 feature
y = 3 * X + 2 + 0.1 * np.random.randn(1000, 1)  # y = 3x + 2 + noise

# Split data into training and testing sets
X_train, X_test = X[:800], X[800:]
y_train, y_test = y[:800], y[800:]

# Define a simple neural network model
model = models.Sequential([
    layers.Input(shape=(1,)),  # Input layer with 1 feature
    layers.Dense(10, activation='relu'),  # Hidden layer with 10 neurons
    layers.Dense(1)  # Output layer with 1 neuron (for regression)
])

# Compile the model
model.compile(optimizer='adam', loss='mean_squared_error')

# Train the model
history = model.fit(X_train, y_train, epochs=50, validation_split=0.2)

# Evaluate the model on the test set
test_loss = model.evaluate(X_test, y_test)
print(f"Test Loss: {test_loss}")

# Make predictions
predictions = model.predict(X_test)

# Print some predictions and actual values
for i in range(5):
    print(f"Predicted: {predictions[i][0]}, Actual: {y_test[i][0]}")