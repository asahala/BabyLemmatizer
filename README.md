![alt text](https://www.mv.helsinki.fi/home/asahala/img/babylemmatizer.png)

# BabyLemmatizer 2.0
State-of-the-art neural tagger and lemmatizer for Akkadian (and other cuneiform languages). ***This repository will be officially published and documented in late February 2023. Before that some files may be missing and the system cannot be used. This disclaimer will be removed after the official publication.***

BabyLemmatizer 2.0 is fully based on OpenNMT, which makes it simpler to use than the previous BabyLemmatizer version that was dependent on an outdated version of TurkuNLP with some problematic dependencies. At its current stage, BabyLemmatizer can be used for part-of-speech tagging and lemmatization of transliterated Akkadian texts. Unlike the old version, BabyLemmatizer 2.0 uses an unindexed character based representation for syllabic signs and sign-based tokenization for logograms, that maximize its capability to discriminate between predictable and suppletive grapheme to phoneme relations.

### Brief description
BabyLemmatizer 2.0 approaches POS-tagging and lemmatization as a Machine Translation task. It features context-aware POS-tagger and lemmatizer that combine strenghts of encoder-decoder neural networks, and (very slightly) statistical and heuristic dictionary-based methods to post-correct and score the reliability of the annotations.

### Performance
Results of the 5-fold cross-validation of the first millennium Babylonian models trained with 500k examples split into 80/10/10.

|category|avg.|lbtest1|lbtest2|lbtest3|lbtest4|lbtest5|conf. int|
|---|---|---|---|---|---|---|---|
|tagger|**97.42%**|97.40%|97.44%|97.33%|97.49%|97.46%|±0.06%|
|lemmatizer|**94.75%**|94.55%|94.71%|94.71%|94.78%|95.01%|±0.15%|
|tagger+lemmatizer|**94.62%**|94.36%|94.61%|94.62%|94.69%|94.81%|±0.14%|

## Requirements
1. [OpenNMT-py](https://github.com/OpenNMT/OpenNMT-py)
2. Python 3.6+

BabyLemmatizer 2.0 has been tested with Python 3.9 and OpenNMT-py 3.0.

## Setting up BabyLemmatizer
The easiest way to get BabyLemmatizer 2.0 running is to create a Python 3.9 virtual environment for OpenNMT-py, this ensures that you have permanently all necessary requirements installed and they do not conflict with your other libaries. For example,

1. ```python3.9 -m venv OpenNMT```
2. ```source OpenNMT/bin/activate```
3. ```pip install --upgrade pip```
4. ```pip install OpenNMT-py```

Then you need to clone **BabyLemmatizer** reposotory and edit ```preferences.py``` to add paths to the virtual environment and OpenNMT binaries. 

```
python_path = '/yourpath/OpenNMT/bin/'
onmt_path = '/yourpath/OpenNMT/lib/python3.9/site-packages/onmt/bin'
``` 

After this, you can run ```preferences.py``` and if lots of OpenNMT documentation prints on your screen, everything should be okay.

## Use in Python

### Lemmatization
To tag and lemmatize texts, you need to first convert it into a CoNLL-U format. See instructions in the [conllu](https://github.com/asahala/BabyLemmatizer/tree/main/conllu) folder.

Use ```lemmatizer_pipeline.py``` to annotate your texts. If you have an empty CoNLL-U file in in the ```input``` folder named ```example.conllu```, and you want to tag and lemmatize it using the first millennium Babylonian model ```lbtest1```, you can do it with two lines of code:

```
l = Lemmatizer('./input/example.conllu') 
l.run_model('lbtest1', cpu=True) # assuming that you want to use CPU instead of GPU
```
Lemmatization may take a while depending on your hardware. Your result will be saved as ```input/example_lemmatized.conllu```. 

**Note:** prior to official publishing of this repository, post-processing is not done.

### Training models
To train a new model, put your source files in the ```conllu``` folder. Then then proceed with the following steps using ```train_pipeline.py``` script. Let's assume you have CoNLL-U train/dev/test files with prefixes ```elamite``` and ```assyrian```. Train the models with two lines of code:

```
build_train_data("elamite", "assyrian")
train_model("elamite", "assyrian")
```

See more information about the input format in the [conllu](https://github.com/asahala/BabyLemmatizer/tree/main/conllu) foder.

### Evaluating models
You can perform n-fold cross-validation of your models by using ```evaluate_models.py```. For example, to evaluate five Elamite models, call the method ```pipeline("elamite1", "elamite2", "elamite3", "elamite4", "elamite5")```.

All intermediate steps of evaluation are saved into ```models/model_name/eval/``` and the final lemmatization results are saved into ```output_final.conllu2``` in this folder.


## Command line use

BabyParser 2.0 can be used directly from the command line.

### Lemmatization
To lemmatize unlemmatized corpus, run the following command:

```python3 babylemmatizer.py --filename corpus_file --lemmatize modelname```

where ```corpus_file``` points to the CoNLL-U file you want to lemmatize and ```modelname``` to the model you want to use. Lemmatization is by default done on GPU, but if you don't have a CUDA cabable GPU, you can add parameter ```--use-cpu```.

### Training and evaluation
Training and evaluation can be done using ```babylemmatizer.py``` command line API. The command line interface is purposefully simple and does not give user direct access to any additional parameters.

```
--build-data  <arg>                  Builds data from CoNNL-U files in your conllu folder
--train-model <arg>                  Trains a model or models for the built data
--build-train <arg>                  Builds data and trains a model or models
--evaluate    <arg>                  Cross-validates your model or models
```

All these commands have one mandatory argument, which points to the data in your ```conllu``` folder if you are building new data, or to your ```models``` folder if you are training or evaluating models. For example, if you have CoNLL-U files ```assyrian-train.conllu, assyrian-dev.conllu, assyrian-test.conllu``` and want to build data and train models for them, you can call BabyLemmatizer ```python babylemmatizer.py --build-train assyrian```. In case you want to train several models for 10-fold cross-validation, you can have train/dev/test CoNLL-U files with prefixes ```assyrian0, assyrian1, ..., assyrian9``` and use the command ```python babylemmatizer.py --build-train assyrian*```. Similarly, to cross-validate these models after training, use ```python babylemmatizer.py --evaluate assyrian*```.

Some additional commands:

```
--normalize-conllu            Attempts to normalize transliteration in all files in your conllu folder.
```


## Citations
If you use BabyLemmatizer for annotating your data or training new models, please cite this repository and [Sahala et al. 2022](http://hdl.handle.net/10138/348412). An updated publication will be written in 2023 that describes this version of the system.

```
@inproceedings{sahala2022babylemmatizer,
  title={BabyLemmatizer: A Lemmatizer and POS-tagger for Akkadian},
  author={Sahala, Aleksi and Alstola, Tero and Valk, Jonathan and Linden, Krister},
  booktitle={CLARIN Annual Conference Proceedings, 2022},
  year={2022},
  organization={CLARIN ERIC}
}
```

## Upcoming features
In order of priority:

* Pretrained models
* Advanced command-line use (tuning the neural net, customizing folders etc)
* Phonological transcription
* Direct Oracc ATF support
* Morphological analysis
* Server-side use
* Machine Translation
