![alt text](https://www.mv.helsinki.fi/home/asahala/img/babylemmatizer2.png)

# BabyLemmatizer 2.0
State-of-the-art neural part-of-speech-tagger and lemmatizer finetuned for Cuneiform languages such as Akkadian, Sumerian and Urartian. BabyLemmatizer models also exist for other ancient languages such as Ancient Greek.

BabyLemmatizer 2.0 is fully based on OpenNMT, which makes it simpler to use than the previous BabyLemmatizer version that was dependent on an outdated version of TurkuNLP with some problematic dependencies. At its current stage, BabyLemmatizer can be used for part-of-speech tagging and lemmatization of transliterated Akkadian texts. Unlike the old version, BabyLemmatizer 2.0 uses an unindexed character based representation for syllabic signs and sign-based tokenization for logograms, that maximize its capability to discriminate between predictable and suppletive grapheme to phoneme relations. For network architecture and encoding of the input sequences, see [this description](network.md).

### Brief description
BabyLemmatizer 2.0 approaches POS-tagging and lemmatization as a Machine Translation task. It features a POS-tagger and lemmatizer that combine strengths of encoder-decoder neural networks (i.e. predicting analyses for unseen word forms), and (at the moment very slightly) statistical and heuristic dictionary-based methods to post-correct and score the reliability of the annotations. BabyLemmatizer is useful for making Akkadian texts searchable and useable for other Natural Language Processing tasks, such as building [Word Embeddings](https://github.com/asahala/pmi-embeddings), as transliterated texts are practically impossible to use efficiently due to orthographic and morphological complexity of the language.

|***Transliteration*** | ***Lemma*** | ***POS-tag*** |
| --- | --- | --- |
| IMIN{+et}	| sebe | NU |
| a-di | adi | PRP |
| IMIN{+et} | sebe | NU |
| a-ra-an-šu | arnu | N |
| pu-uṭ-ri | paṭāru | V |

# Requirements
1. [OpenNMT-py](https://github.com/OpenNMT/OpenNMT-py)
2. Python 3.6+ (for BabyLemmatizer and 3.9 for OpenNMT virtual environment)

BabyLemmatizer 2.0 has been tested with Python 3.9 and OpenNMT-py 3.0.

# Setting up BabyLemmatizer
The easiest way to get BabyLemmatizer 2.0 running is to create a Python 3.9 virtual environment for OpenNMT-py. This ensures that you have permanently all necessary requirements installed and they do not conflict with your other libraries. This is fairly simple to do:

1. ```python3.9 -m venv OpenNMT```
2. ```source OpenNMT/bin/activate```
3. ```pip install --upgrade pip```
4. ```pip install OpenNMT-py```

Then you need to clone the **BabyLemmatizer** repository and edit ```preferences.py``` to add paths to the virtual environment and OpenNMT binaries. 

```
python_path = '/yourpath/OpenNMT/bin/'
onmt_path = '/yourpath/OpenNMT/lib/python3.9/site-packages/onmt/bin'
``` 

Now you can run ```preferences.py``` and if lots of OpenNMT documentation prints on your screen, everything should be okay.

# Quick guide
See [BabyLemmatizer Manual](https://docs.google.com/document/d/1j11N2bsIEcuZpAzJP1wmVaWrsjd0ml3HF7K-PK0AXdQ/) for instructions how to lemmatize the demo text.

# Use in Python

## Input and output format
BabyLemmatizer uses CoNLL-U+ format. You can read more about it here [conllu](https://github.com/asahala/BabyLemmatizer/tree/main/conllu).

### Lemmatization
To tag and lemmatize texts, you need to first convert it into a CoNLL-U format. See instructions in the [conllu](https://github.com/asahala/BabyLemmatizer/tree/main/conllu) folder.

Use ```lemmatizer_pipeline.py``` to annotate your texts. If you have an empty CoNLL-U file in the ```input``` folder named ```example.conllu```, and you want to tag and lemmatize it using the first millennium Babylonian model ```lbtest1```, you can do it with two lines of code:

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
You can perform n-fold cross-validation of your models by using ```evaluate_models.py```. For example, to evaluate five Elamite models using CPU, call the method ```pipeline("elamite1", "elamite2", "elamite3", "elamite4", "elamite5", cpu=True)```.

All intermediate steps of evaluation are saved into ```models/model_name/eval/``` and the final lemmatization results are saved into ```output_final.conllu2``` in this folder.


# Command line use

BabyParser 2.0 can be used directly from the command line.

### Lemmatization
To lemmatize unlemmatized corpus, run the following command:

```python3 babylemmatizer.py --lemmatize=modelname --filename=corpus_file```

where ```corpus_file``` points to the CoNLL-U file (e.g. ```input/example.conllu```) you want to lemmatize and ```modelname``` to the model you want to use. Lemmatization is by default done on GPU, but if you don't have a CUDA capable GPU, you can add parameter ```--use-cpu```.

### Training and evaluation
Training and evaluation can be done using ```babylemmatizer.py``` command line API. The command line interface is purposefully simple and does not give user direct access to any additional parameters.

```
GENERAL PARAMETERS (use only one)
--build=<arg>                  Builds data from CoNNL-U files in your conllu folder
--train=<arg>                  Trains a model or models from the built data
--build-train=<arg>            Builds data and trains a model or models
--evaluate=<arg>               Evaluates and cross-validates your model or models
--evaluate-fast=<arg>          Rerun evaluation without running POS-tagger and lemmatizer
                               (in case you have ran them already and just want to see the results again)

PATH AND OPTIONS
--use-cpu                      Use CPU instead of GPU (read more below)
--conllu-path=<arg>            Path where to read CoNLL-U files
--model-path=<arg>             Path where to save/read models  
```

All these parameters have one mandatory argument, which points to the data in your ```conllu``` folder if you are building new data, or to your ```models``` folder if you are training or evaluating models. For example, if you have CoNLL-U files ```assyrian-train.conllu, assyrian-dev.conllu, assyrian-test.conllu``` and want to build data and train models for them, you can call BabyLemmatizer ```python babylemmatizer.py --build-train=assyrian```. In case you want to train several models for n-fold cross-validation, you can have train/dev/test CoNLL-U files with prefixes followed by numbers, e.g. with n=10 ```assyrian0, assyrian1, ..., assyrian9``` and use the command ```python babylemmatizer.py --build-train=assyrian*```. Similarly, to cross-validate these models after training, use ```python babylemmatizer.py --evaluate=assyrian*```.

***Using CPU:*** If you want to use CPU instead of GPU (i.e. if you get a CUDA error), use parameter ```--use-cpu``` in addition with parameters ```--train, --build-train``` and ```--evaluate```. Note that training models with CPU is extremely slow and may take days depending on your training data size and hardware. However, you can lemmatize new texts using CPU without too much waiting.

Some additional commands:

```
--normalize-conllu            Attempts to normalize transliteration in all files in your conllu folder (just for testing purposes)
```

# Performance

By using all relevant data from Oracc and a 80/10/10 train/dev/test sets. 1st Bab = all first millennium Babylonian texts.

![alt text](https://www.mv.helsinki.fi/home/asahala/img/summary2.png)

<!--
# Performance
This section presents 10-fold cross-validated evaluation results for various cuneiform languages using 80/10/10 split and their confidence intervals (CI). Evaluation is ran component by component (POS-tagger, lemmatizer and POS-tagger+lemmatizer combined) ignoring fully broken words. Evaluation is ran also separately for OOV words to show model's ability to deal with previously unseen word forms. The performance is measured in accuracy.

![alt text](https://www.mv.helsinki.fi/home/asahala/img/formula2.png)

Evaluation is performed for the Neural Net output and for the Post-Corrected output separately. The improvement is very slight compared to BabyLemmatizer 1.0, where the NN performed on average 10-15% worse.

Average results are shown in the AVG column.

## Summary
Summary of the evaluation results. Detailed information below.

![alt text](https://www.mv.helsinki.fi/home/asahala/img/summary2.png)

### Urartian
Total data set size ca. 20k words (including lacunae).

![alt text](https://www.mv.helsinki.fi/home/asahala/img/urartian-eval2.png)

### Neo-Assyrian
Total data set size ca. 330k words (including lacunae). Consists of all Oracc texts labeled as Neo-Assyrian.

![alt text](https://www.mv.helsinki.fi/home/asahala/img/neoass-eval.png)

### First Millennium Babylonian
Total data set size ca. 1.3M words (including lacunae). Consists of all Oracc texts labeled as any variant of Babylonian or Akkadian in the first millennium BCE. Neo-Assyrian excluded. OOV rate is fairly low but the data set is very varied and comprises all different text genres.

![alt text](https://www.mv.helsinki.fi/home/asahala/img/neobab-eval.png)

### Sumerian (Literary)
Total data set size ca. 270k words (including lacunae). Consists of all Sumerian literary texts in EPSD2/Literary, EPSD2/earlylit and EPSD/Praxis*. Note the very high amount of OOV words in this data set. Subscript indices were not removed from the Sumerian data as homophones with different indices can belong to different POS-classes.

![alt text](https://www.mv.helsinki.fi/home/asahala/img/sumlit-eval.png)

### Sumerian (Administrative)
Total data set size ca. 570k words (including lacunae). Consists of all Sumerian Early Dynastic, Old Babylonian, Old Akkadian, Ebla and Lagaš II administrative texts in EPSD2. Ur III corpus was left out as it would have completely dominated the data set. OOV rate is fairly low. Indices were preserved as above.

![alt text](https://www.mv.helsinki.fi/home/asahala/img/sumadm-eval.png)

## Non-cuneiform languages
### Ancient Greek
Total data set size ca. 560k words. Consists of the Greek data from [PerseusDL](http://perseusdl.github.io/treebank_data/) treebank. Empty lemmata and POS-tags removed and POS-tags simplified by removing [morphological annotation](https://github.com/cltk/greek_treebank_perseus) (i.e. only predicting the first character in the postag-sequence). Morphological feats will be predicted later. Post-processing does not improve results with Ancient Greek.

![alt text](https://www.mv.helsinki.fi/home/asahala/img/sgreek-eval2.png)
-->

# Citations
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

# Upcoming features
In order of priority:

* Pretrained models (late feb or early march)
* Advanced command-line use (tuning the neural net, customizing folders etc)
* Phonological transcription
* Morphological analysis
* Named-entity recognition
* Direct Oracc ATF support (E. Pagé-Perron has perhaps already done ATF<->CoNLL-u scripts)
* Server-side use

# Bugs
* If user forgets = between parameter and argument in command line use, things go wrong


# Todo
* [DONE] --lemmatize to work with conlluplus
* conf score-wise evaluation
* [DONE] lemmatization cycle as automatic as possible
* [DONE] write-protected fields
* model versioning
* global __version__ and logger
* [DONE but needs CMD params] adjustable context window
* [DONE] normalize function for conlluplus
* data splitter for conlluplus
* [DONE] force determinative capitalization for train data
* remove unused code
* Oracc guideword field for conllu+

If willpower

* rewrite conllu+ class in a way that updates can be done on the fly instead of reiterating
* tag confusion matrix
* tag-wise evaluation
* category-wise evaluation (logo/logosyll/syll)
* add possibility to use external validation set
