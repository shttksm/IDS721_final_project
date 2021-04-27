from flask import Flask
app = Flask(__name__)

import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

bucket_name = "gs://final-project-bukect2"
# Change here!
train_data = "gs://final-project-bucket2/algorithms-demo/data/train.csv"

@app.route('/')
def load_test():
    return 'Hello, World!'

@app.route('/train')
def train():
    global CLF
    global y_LT
    global X_LT

    # read training dataset
    df = pd.read_csv(train_data)
    # create dataset
    ncol = len(df)
    # First label, y
    y = np.zeros((ncol,))
    y[np.where(df.iloc[:, 0].values == ">50K")] = 1

    # second, features, X
    # Because this is the first version, I just remain numerical columns
    # Later, I can do one-hot encording or something like that to convert from string column to categorical one
    X = df.iloc[:, [1, 3, 5, 11, 12, 13]].values

    # Make a classifier
    clf = RandomForestClassifier(random_state=0)

    # Fit and evauate the training acc
    clf.fit(X, y)
    y_pred = clf.predict(X)
    acc = accuracy_score(y, y_pred)

    # Save the model as a global.
    CLF = clf
    # Save the load test samples as globals.
    y_LT = y[0]
    X_LT = X[0].reshape((1, X[0].shape[0]))
    
    return f"Training accuracy is .{acc}"

@app.route('/predict')
def predict():
    global CLF
    global y_LT
    global X_LT

    message = ""
    if CLF is None or y_LT is None or X_LT is None:
        message = "Please visit /train first!"
    else:
        y_pred = CLF.predict(X_LT)
        message = f"Features {X_LT}: Estimated probability {y_pred}"
    return message
                         
if __name__ == "__main__":
    global CLF
    global y_LT
    global X_LT

    # the trained classifier via /tain page, to use other pages, I save it after the tarining as a global value.
    CLF = None
    y_LT = None
    X_LT = None

    app.run(host='0.0.0.0')
