# BabyLemmatizer 2.0
State-of-the-art neural tagger and lemmatizer for Akkadian (and other cuneiform languages). ***This repository will be officially published and documented in late February 2023.***

## Requirements
1. [OpenNMT-py](https://github.com/OpenNMT/OpenNMT-py)
2. Python 3.6+

BabyLemmatizer 2 has been tested with Python 3.9 and OpenNMT-py 3.0.

## Setting it up
The easiest way to get BabyLemmatizer 2 running is to create a Python 3.9 virtual environment for OpenNMT-py, this ensures that you have permanently all necessary requirements installed and they do not conflict with your other libaries. For example,

1. ```python3.9 -m venv OpenNMT```
2. ```source OpenNMT/bin/activate```
3. ```pip install --upgrade pip```
4. ```pip install OpenNMT-py```

Then you need to edit ```preferences.py``` to add paths to the virtual environment and OpenNMT binaries. 

```python_path = '/yourpath/OpenNMT/bin/'```
```onmt_path = '/yourpath/OpenNMT/lib/python3.9/site-packages/onmt/bin'``` 

After this, everything should run.

## Training models
To train a new model, put your source files in the ```conllu``` folder. Then then proceed with the following steps using ```train_pipeline.py``` script:

1. Run method ```build_train_data()```. This method converts the data in the ```conllu``` folder into suitable format.
2. Run method ```train_models()``` with arguments pointing to your model names in the ```conllu``` folder, for example ```train_models("assyrian", "babylonian")```.

See more information about the input format in the ```conllu``` foder.

## Using models
...
