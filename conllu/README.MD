# Conll-u files for training the models
The files must be named as follows ```modelname-type.conllu```, where *modelname* is an arbitrary name that describes your model, *type* is either ```train```, ```test``` or ```dev``` depending on the function of your dataset. For example: ```latebabylonian-train.conllu```, ```latebabylonian-dev.conllu``` and ```latebabylonian-test.conllu```.

The standard practice is to use 80% of your training corpus as the train data, and split the remaining 20% into test and dev data.
