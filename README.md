# BabyLemmatizer 2.0
State-of-the-art neural tagger and lemmatizer for Akkadian (and other cuneiform languages). ***This repository will be officially published and documented in late February 2023.***

## Requirements
...

## Training models
To train a new model, put your source files in the ```conllu``` folder. Then then proceed with the following steps using ```train_pipeline.py``` script:

1. Run method ```build_train_data()```. This method converts the data in the ```conllu``` folder into suitable format.
2. Run method ```train_models()``` with arguments pointing to your model names in the ```conllu``` folder, for example ```train_models("assyrian", "babylonian")```.

See more information about the input format in the ```conllu``` foder.

## Using models
...
