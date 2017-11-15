import os # ONLY USE THIS IF YOU DONT HAVE A GPU
os.environ["CUDA_VISIBLE_DEVICES"] = '-1' # ONLY USE THIS IF YOU DONT HAVE A GPU
import argparse
import numpy
import pandas
import sys
from keras.models import Sequential,model_from_json
from keras.layers import Dense
from keras.utils import np_utils
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import MinMaxScaler
from keras import backend as K
import numpy as np
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

seed = 7


def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


# from keras /
# https://github.com/fchollet/keras/issues/5400#issuecomment-325383549
# they will only work on binary classification problems


def f1_score(y_true, y_pred):

    # Count positive samples.
    c1 = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    c2 = K.sum(K.round(K.clip(y_pred, 0, 1)))
    c3 = K.sum(K.round(K.clip(y_true, 0, 1)))

    # If there are no true samples, fix the F1 score at 0.
    if c3 == 0:
        return 0

    # How many selected items are relevant?
    precision = c1 / c2

    # How many relevant items are selected?
    recall = c1 / c3

    # Calculate f1_score
    f1_score = 2 * (precision * recall) / (precision + recall)
    return f1_score


def precision(y_true, y_pred):

    # Count positive samples.
    c1 = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    c2 = K.sum(K.round(K.clip(y_pred, 0, 1)))
    c3 = K.sum(K.round(K.clip(y_true, 0, 1)))

    # If there are no true samples, fix the F1 score at 0.
    if c3 == 0:
        return 0

    # How many selected items are relevant?
    precision = c1 / c2

    return precision


def recall(y_true, y_pred):

    # Count positive samples.
    c1 = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    c3 = K.sum(K.round(K.clip(y_true, 0, 1)))

    # If there are no true samples, fix the F1 score at 0.
    if c3 == 0:
        return 0

    recall = c1 / c3

    return recall


def loadDataset(filename, header, separator, scale):

        if header is False:
            if ' ' in separator:
                tmpdataframe = pandas.read_csv(filename, header=None,
                                               delim_whitespace=True)
            else:
                tmpdataframe = pandas.read_csv(filename, header=None,
                                               sep=separator)
        else:
            if ' ' in separator:
                tmpdataframe = pandas.read_csv(filename, header=None,
                                               delim_whitespace=True)
            else:
                tmpdataframe = pandas.read_csv(filename, header=None,
                                               sep=separator)
        dataframe = tmpdataframe
        print("loading dataset %s" % filename)
        dataframe = dataframe.sort_values(by=len(dataframe.columns.tolist())-1)
        cols = list(dataframe)
        if scale is True:
            print("scaling enabled, scaling all the columns in the dataset.")
            for col in cols:
                scaler = MinMaxScaler()
                dataframe[col] = scaler.fit_transform(dataframe[col])
        datavalues = dataframe.values
        X = datavalues[:, 0:len(dataframe.columns.tolist())-1]
        Y = datavalues[:, len(dataframe.columns.tolist())-1]
        return X, Y


def makepercentile(inpset, percentile):
        n = len(inpset)
        frac = n*percentile
        ni = math.ceil(frac)
        return inpset[ni]


def middle(n1, n2):
        return n1+n2/2.0


def makeequalfreqbins(inpset, nbins):
        frac = 1.0/nbins
        ret = []
        # ret.append(inpset[0])
        for i in range(0, nbins):
                ret.append(makepercentile(inpset, i*frac))
        ret.append(inpset[len(inpset)-1]+1)
        return ret


def meta_larger_model(n, inp, networklayers):
    def int_larger_model():
        # create model
        model = Sequential()
        model.add(Dense(inp, input_dim=inp, init='random_uniform',
                        activation='sigmoid'))
        if networklayers is not None:
            print("making custom network config inp->%s->outp" % networklayers)
            for layer in networklayers:
                model.add(Dense(int(layer),
                                kernel_initializer="random_uniform",
                                activation='sigmoid'))
        else:
            print("making default network config inp->300->30->30->outp")
            model.add(Dense(300, kernel_initializer='random_uniform',
                            activation='sigmoid'))
            model.add(Dense(30, kernel_initializer='random_uniform',
                            activation='sigmoid'))
            model.add(Dense(30, kernel_initializer='random_uniform',
                            activation='sigmoid'))

        print("making ann with %s outputs " % n)
        model.add(Dense(n, init='random_uniform', activation='softmax'))
        model.compile(loss='categorical_crossentropy', optimizer='rmsprop',
                      metrics=['accuracy'])
        return model
    return int_larger_model


def testClassificationOnNClasses(X, Y, n, epochs, savemodelfile, loadmodelfile,
                                 figprefix, networklayers):
        print("Running classification with %s classes" % n)
        bins = makeequalfreqbins(Y, n)
        if Y.dtype == object:
            print("recoding the Y array")
            Y = np.vstack(Y[:]).astype(np.float)
        inds = np.digitize(Y, bins)
        # encode class values as integers
        encoder = LabelEncoder()
        encoder.fit(inds)
        tmp_encoded_Y = encoder.transform(inds)
        # convert integers to dummy variables (i.e. one hot encoded)
        encoded_y = np_utils.to_categorical(tmp_encoded_Y)
        model = None
        if loadmodelfile is None:
            my_larger_model_fn = meta_larger_model(n, X.shape[1],
                                                   networklayers)
            model = my_larger_model_fn()
        else:
            model = loadmodel(loadmodelfile)
        history = model.fit(X, encoded_y, validation_split=0.1,
                            shuffle=True, epochs=epochs, batch_size=32)

        # summarize history for accuracy
        fig, ax = plt.subplots()
        plt.plot(history.history['acc'])
        plt.plot(history.history['val_acc'])
        plt.title('model accuracy')
        plt.ylabel('accuracy')
        plt.xlabel('epoch')
        plt.legend(['acc', 'val_acc'], loc='upper left')
        plt.show()
        fig.savefig(figprefix+"fig-plot-acc.pdf")
        plt.clf()
        fig, ax = plt.subplots()
        # summarize history for loss
        plt.plot(history.history['loss'])
        plt.plot(history.history['val_loss'])
        plt.title('model loss')
        plt.ylabel('loss')
        plt.xlabel('epoch')
        plt.legend(['loss', 'val_loss'], loc='upper left')
        fig.savefig(figprefix+"fig-plot-loss.pdf")

        if savemodelfile is not None:
            savemodel(model, savemodelfile)

def savemodel(model, modelfile):
    # serialize model to JSON
    model_json = model.to_json()
    with open(modelfile+".json", "w") as json_file:
        json_file.write(model_json)
        # serialize weights to HDF5
        model.save_weights(modelfile+".h5")
        print("saved model object to %s and weights to %s "
              % (modelfile+".json", modelfile+".h5"))


def loadmodel(modelfile):
    # load json and create model
    json_file = open(modelfile+".json", 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    loaded_model = model_from_json(loaded_model_json)
    # load weights into new model
    loaded_model.load_weights(modelfile+".h5")
    print("Loaded model from disk")
    loaded_model.compile(loss='categorical_crossentropy', optimizer='rmsprop',
                         metrics=['accuracy'])
    return loaded_model


def printfigs(predicted, real):
        print("predicted.shape: %s , real.shape: %s"
              % (predicted.shape, real.shape))
        fig, ax = plt.subplots()
        ax.scatter(real, predicted)
        ax.plot([real.min(), real.max()], [real.min(), real.max()], 'k--',
                lw=4)
        ax.set_xlabel('Measured')
        ax.set_ylabel('Predicted')
        fig.savefig("fig-scatter.pdf")
        # fix random seed for reproducibility
        fig, ax = plt.subplots()
        line1, = ax.plot(real, label='real')
        line2, = ax.plot(predicted, label='predicted')
        plt.legend(handles=[line1, line2])

        ax.set_xlabel('Event')
        ax.set_ylabel('Fish caught')
        fig.savefig("fig-plot.pdf")


def main():

    parser = argparse.ArgumentParser(description='train NN classification'
                                     + ' model on regression dataset!')
    parser.add_argument('--classes', metavar='N', type=int,
                        help='How many classes to use in the classification'
                        + ' within the floating point set')
    parser.add_argument('--epochs', metavar='epochs', type=int,
                        help='How many epochs')
    parser.add_argument('--datasetfile', metavar='datasetfile', type=str,
                        help='Datasetfile')
    parser.add_argument('--datasetheader', metavar='True/False', type=str2bool,
                        help='Does the dataset contain a datasetheader'
                        + ' or not (Bool)')
    parser.add_argument('--separator', metavar='\'<sep>\'', type=str,
                        help='separator')
    parser.add_argument('--figprefix', metavar='figprefix', type=str,
                        help='Prefix for figure files')
    parser.add_argument('--scale', metavar='True/False', type=str2bool,
                        help='Scale the input dataset to range [0,1] (Bool)')
    parser.add_argument('--savemodel', metavar='<filename>', type=str,
                        help='Save the model to file <filenameprefix>{.json,.h5}')
    parser.add_argument('--loadmodel', metavar='<filename>', type=str,
                        help='Load the model from file <filenameprefix>{.json,.h5}')
    parser.add_argument('--networklayer', action='append', help='Add a network'
                        + ' layer, this is additive, so multiple calls to this'
                        + ' option will add multiple layers. Not applicable'
                        + ' when loading model from file.', required=True)


    args = parser.parse_args()

    if not len(sys.argv) > 1:
        print ("not enough arguments")
        parser.print_help()
        sys.exit(1)
    X = Y = None
    X, Y = loadDataset(args.datasetfile, args.datasetheader,
                       args.separator, args.scale)
    numpy.random.seed(seed)
    testClassificationOnNClasses(X, Y, args.classes,
                                 args.epochs, args.savemodel,
                                 args.loadmodel, args.figprefix,
                                 args.networklayer)


if __name__ == "__main__":
    main()
