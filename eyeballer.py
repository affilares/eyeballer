#!/usr/bin/python3

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from keras.preprocessing.image import ImageDataGenerator
from keras.models import Sequential, Model
from keras.optimizers import RMSprop, Adam
from keras.layers import Conv2D, MaxPooling2D
from keras.layers import Activation, Dropout, Flatten, Dense
from keras.callbacks import TensorBoard
from keras import regularizers

from PIL import Image
from sklearn.metrics import classification_report, confusion_matrix
from keras.applications.inception_v3 import InceptionV3
from keras.applications import MobileNet

import numpy as np
import matplotlib.pyplot as plt

import os
import argparse
import shutil

# Hyperparams
#IMAGE_WIDTH, IMAGE_HEIGHT = 360, 225
IMAGE_WIDTH, IMAGE_HEIGHT = 224, 224

TEST_FILE = "test_file.txt"
WEIGHTS_FILE = "weights.h5"

# Parse the arguments
parser = argparse.ArgumentParser(description='Give those screenshots of yours a quick eyeballing')
parser.add_argument("--modelfile", help="Weights file for input/output")
parser.add_argument("--batchsize", help="Batch size", default=32, type=int)
parser.add_argument("--epochs", help="Number of epochs", default=20, type=int)
args = parser.parse_args()

if args.modelfile:
    WEIGHTS_FILE = args.modelfile
BATCH_SIZE = args.batchsize
EPOCHS = args.epochs

input_shape = (IMAGE_WIDTH, IMAGE_HEIGHT, 3)

#base_model = InceptionV3(weights='imagenet', include_top=False, input_shape=input_shape)
base_model = MobileNet(weights='imagenet', include_top=False, input_shape=input_shape)
x = base_model.output
x = Conv2D(3, (2, 2), kernel_regularizer=regularizers.l2(0.01))(x)
x = MaxPooling2D(pool_size=(2, 2), name="LastPooling")(x)
x = Dropout(0.2)(x)

x = Flatten()(x)

x = Dense(4, activation="relu", name="HiddenLayer1", kernel_regularizer=regularizers.l2(0.01))(x)
x = Dropout(0.2)(x)
x = Dense(4, activation="relu", name="HiddenLayer2", kernel_regularizer=regularizers.l2(0.01))(x)
x = Dropout(0.2)(x)
x = Dense(4, activation="relu", name="HiddenLayer3", kernel_regularizer=regularizers.l2(0.01))(x)
x = Dropout(0.2)(x)
# x = Dense(8,x = Dense(4, activation="relu", name="HiddenLayer1", kernel_regularizer=regularizers.l2(0.01))(x)
# x = Dense(16, activation="relu", name="HiddenLayer3", kernel_regularizer=regularizers.l2(0.01))(x)
# x = Dropout(0.5)(x)
output_layer = Dense(1, activation="sigmoid", name="OutputLayer")(x)

model = Model(inputs=base_model.input, outputs=output_layer)

for layer in base_model.layers:
    layer.trainable = False

adam = Adam(lr=.01)
model.compile(loss='binary_crossentropy',
              optimizer="rmsprop",
              metrics=['accuracy'])

if args.modelfile:
    if os.path.isfile(WEIGHTS_FILE):
        model.load_weights(WEIGHTS_FILE)
        print("Loaded model from file.")
    else:
        print("No model to load from file")

print(model.summary())

# Data augmentation
data_generator = ImageDataGenerator(
    rescale=1./255,
    shear_range=0.2,
    zoom_range=0.2,
#    color_mode="grayscale",
    samplewise_center=True,
    validation_split=0.2,
    horizontal_flip=False)

# Data preparation
training_generator = data_generator.flow_from_directory(
    "images/",
    target_size=(IMAGE_WIDTH, IMAGE_HEIGHT),
    batch_size=BATCH_SIZE,
    subset='training',
    class_mode="binary")
validation_generator = data_generator.flow_from_directory(
    "images/",
    target_size=(IMAGE_WIDTH, IMAGE_HEIGHT),
    batch_size=BATCH_SIZE,
    subset='validation',
    shuffle=False,
    class_mode="binary")

# Training
history = model.fit_generator(
    training_generator,
    steps_per_epoch=len(training_generator.filenames) // BATCH_SIZE,
    epochs=EPOCHS,
    validation_data=validation_generator,
    validation_steps=len(validation_generator.filenames) // BATCH_SIZE,
    verbose=1)

# Plot training & validation accuracy values
plt.plot(history.history['acc'])
plt.plot(history.history['val_acc'])
plt.title('Model accuracy')
plt.ylabel('Accuracy')
plt.xlabel('Epoch')
plt.legend(['Train', 'Validation'], loc='upper left')
plt.savefig("accuracy.png")
plt.clf()
plt.cla()
plt.close()

# Plot training & validation loss values
plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('Model loss')
plt.ylabel('Loss')
plt.xlabel('Epoch')
plt.legend(['Train', 'Validation'], loc='upper left')
plt.savefig("loss.png")

if args.modelfile:
    print("Saving model...")
    model.save_weights(WEIGHTS_FILE)
    print("Model saved")

def confusion_matrix_evaluate(validation_generator, model):
    #Confution Matrix and Classification Report
    y_pred = model.predict_generator(validation_generator, verbose=1)
    y_pred = y_pred > 0.5
    print('Confusion Matrix')
    print(confusion_matrix(validation_generator.classes, y_pred))

    j = 0
    for batch in validation_generator:
        labels = batch[1]
        labels = labels > 0.5
        for i in range(len(labels)):
            index = i + (j * BATCH_SIZE)
            # Correct?
            if labels[i] == y_pred[index]:
                shutil.copyfile("images/" + validation_generator.filenames[index], "confusion/correct/" + validation_generator.filenames[index])
            # Wrong
            else:
                shutil.copyfile("images/" + validation_generator.filenames[index], "confusion/wrong/" + validation_generator.filenames[index])
        j+=1

# Print out a confusion matrix in image form!
confusion_matrix_evaluate(validation_generator, model)