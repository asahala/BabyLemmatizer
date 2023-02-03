![alt text](https://www.mv.helsinki.fi/home/asahala/img/babylemmatizer.png)

# BabyLemmatizer 2.0
State-of-the-art neural tagger and lemmatizer for Akkadian (and other cuneiform languages). ***This repository will be officially published and documented in late February 2023.***

BabyLemmatizer 2.0 is fully based on OpenNMT, which makes it simple to use compared to the old BabyLemmatizer version that was dependent on an outdated version of TurkuNLP. At its current stage, BabyLemmatizer can be used for part-of-speech tagging and lemmatization of transliterated Akkadian texts. Unlike the old version, BabyLemmatizer 2.0 uses an unindexed character based representation for syllabic signs and sign-based tokenization for logograms, that maximize its capability to discriminate between predictable and suppletive grapheme to phoneme relations.

BabyLemmatizer 2.0 features context-aware POS-tagger and lemmatizer, that combine strenghts of neural networks, and lightly statistical dictionary-based methods. The current version is able to reach 97.40% accuracy in POS-tagging and 95.00% in lemmatization in a held-out test set (Neo-Babylonian data). If you use BabyLemmatizer for annotating your data or training new models, please cite [Sahala et al. 2022](http://hdl.handle.net/10138/348412). An updated publication will be written in 2023 that describes this version of the system.

## Performance
...

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

## Using models
To tag and lemmatize texts, you need to first convert it into a CoNLL-U format. See instructions in the [conllu](https://github.com/asahala/BabyLemmatizer/tree/main/conllu) folder.

Use ```lemmatizer_pipeline.py``` to annotate your texts. If you have an empty CoNLL-U file in in the ```input``` folder named ```example.conllu```, and you want to tag and lemmatize it using the first millennium Babylonian model ```lbtest1```, you can do it with two lines of code:

```
l = Lemmatizer('./input/example.conllu') 
l.run_model('lbtest1')
```
Lemmatization may take a while depending on your hardware. Your result will be saved as ```input/example_lemmatized.conllu```. 

**Note:** prior to official publishing of this repository, post-processing is not done.

## Training models
To train a new model, put your source files in the ```conllu``` folder. Then then proceed with the following steps using ```train_pipeline.py``` script:

1. Run method ```build_train_data()```. This method converts the data in the ```conllu``` folder into suitable format.
2. Run method ```train_models()``` with arguments pointing to your model names in the ```conllu``` folder, for example ```train_models("assyrian", "babylonian")```.

See more information about the input format in the [conllu](https://github.com/asahala/BabyLemmatizer/tree/main/conllu) foder.

## Evaluating your models
...

## Citations
If you use BabyLemmatizer, cite this paper and repository as long as this version will be officially described:

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
* Phonological transcription
* Direct Oracc ATF and JSON support
* Morphological analysis
* Server-side usage
