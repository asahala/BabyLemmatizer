![alt text](https://www.mv.helsinki.fi/home/asahala/img/lemmatizer2.png)

# BabyLemmatizer 2.1
State-of-the-art neural part-of-speech-tagger and lemmatizer finetuned for Cuneiform languages such as Akkadian, Sumerian and Urartian. BabyLemmatizer models also exist for other ancient languages such as Ancient Greek. 

BabyLemmatizer is fully based on OpenNMT, which makes it simpler to use than the previous BabyLemmatizer version that was dependent on an outdated version of TurkuNLP with some problematic dependencies. At its current stage, BabyLemmatizer can be used for part-of-speech tagging and lemmatization of transliterated Akkadian texts. Unlike the old version, BabyLemmatizer uses an unindexed character based representation for syllabic signs and sign-based tokenization for logograms, that maximize its capability to discriminate between predictable and suppletive grapheme to phoneme relations. For network architecture and encoding of the input sequences, see [this description](network.md). For the user manual of BabyLemmatizer, click [here](https://docs.google.com/document/d/1j11N2bsIEcuZpAzJP1wmVaWrsjd0ml3HF7K-PK0AXdQ/).

### Brief description
BabyLemmatizer approaches POS-tagging and lemmatization as a Machine Translation task. It features a POS-tagger and lemmatizer that combine strengths of encoder-decoder neural networks (i.e. predicting analyses for unseen word forms), and (at the moment very slightly) statistical and heuristic dictionary-based methods to post-correct and score the reliability of the annotations. BabyLemmatizer is useful for making Akkadian texts searchable and useable for other Natural Language Processing tasks, such as building [Word Embeddings](https://github.com/asahala/pmi-embeddings), as transliterated texts are practically impossible to use efficiently due to orthographic and morphological complexity of the language.

|***Transliteration*** | ***Lemma*** | ***POS-tag*** |
| --- | --- | --- |
| IMIN{+et}	| sebe | NU |
| a-di | adi | PRP |
| IMIN{+et} | sebe | NU |
| a-ra-an-šu | arnu | N |
| pu-uṭ-ri | paṭāru | V |

# Requirements
1. [OpenNMT-py](https://github.com/OpenNMT/OpenNMT-py)
2. [Python 3.9+](https://www.python.org/downloads/)

BabyLemmatizer has been tested with Python 3.9 and OpenNMT-py 3.0 and it's highly recommended to use these versions for the virtual environment.

# Setting up BabyLemmatizer
The easiest way to get BabyLemmatizer running is to create a Python 3.9 virtual environment for OpenNMT-py. This ensures that you have permanently all necessary requirements installed and they do not conflict with your other libraries. This is fairly simple to do:

1. make a directory and go there (you need to use this path later)
2. ```python3.9 -m venv OpenNMT```
3. ```source OpenNMT/bin/activate```
4. ```pip install --upgrade pip```
5. ```pip install OpenNMT-py```

Then you need to clone the **BabyLemmatizer** repository and edit ```preferences.py``` to add paths to the virtual environment and OpenNMT binaries. 

```
python_path = '/yourpath/OpenNMT/bin/'
onmt_path = '/yourpath/OpenNMT/lib/python3.9/site-packages/onmt/bin'
``` 

Now you can run ```preferences.py``` and if lots of OpenNMT documentation prints on your screen, everything should be okay.

# Pretrained models
Following pretrained models are available for version 2.1 (and newer): [Sumerian](https://huggingface.co/asahala/BabyLemmatizer-Sumerian) (includes two sub-models: literary and administrative), [Neo-Assyrian](https://huggingface.co/asahala/BabyLemmatizer-Neo-Assyrian), [Middle Assyrian](https://huggingface.co/asahala/BabyLemmatizer-Middle-Assyrian) (augmented model), [First Millennium Babylonian](https://huggingface.co/asahala/BabyLemmatizer-Babylonian-1st) (Late and Neo-Babylonian, Standard Babylonian), [Second Millennium Babylonian](https://huggingface.co/asahala/BabyLemmatizer-Babylonian-2nd) (e.g. Middle Babylonian), [Urartian](https://huggingface.co/asahala/BabyLemmatizer-Urartian), [Latin](https://huggingface.co/asahala/BabyLemmatizer-Latin) (demo), [Ancient Greek](https://huggingface.co/asahala/BabyLemmatizer-Greek) (demo).

To use these models, clone or download the repository you want and extract the ```.tar.gz``` file, e.g. ```tar -xf sumerian-lit.tar.gz``` to the models directory. You can rerun the evaluation with ```python babylemmatizer.py --evaluate=sumerian-lit```. If you want to use custom model path, see command-line parameters how to specify it. To lemmatize a text, see instructions later in this file and the [User Manual](https://docs.google.com/document/d/1j11N2bsIEcuZpAzJP1wmVaWrsjd0ml3HF7K-PK0AXdQ/).

# User Manual
See [BabyLemmatizer Manual](https://docs.google.com/document/d/1j11N2bsIEcuZpAzJP1wmVaWrsjd0ml3HF7K-PK0AXdQ/) for more in-depth instructions how to lemmatize the demo text, train models and evaluate them.

<!--# Use in Python

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

-->

# Command line use
At present, BabyLemmatizer should be used via command line instead of calling it directly in Python.

### Lemmatization
To lemmatize unlemmatized corpus, run the following command:

```python3 babylemmatizer.py --lemmatize=modelname --filename=corpus_file```

where ```corpus_file``` points to the CoNLL-U file (e.g. ```input/example.conllu```) you want to lemmatize and ```modelname``` to the model you want to use. Lemmatization is by default done on GPU, but if you don't have a CUDA capable GPU, you can add parameter ```--use-cpu```. If you use a custom model directory, remember to add ```--model-path=yourpath``` argument.

It is recommended that the file that you are lemmatizing is in some directory, because the lemmatizer produces several output files. For example, if your unlemmatized conllu file is in ```myworkpath/``` use ```--filename=myworkpath/corpus_file```. For more information about lemmatization, see [BabyLemmatizer Manual](https://docs.google.com/document/d/1j11N2bsIEcuZpAzJP1wmVaWrsjd0ml3HF7K-PK0AXdQ/).

### Training and evaluation
Training and evaluation can be done using ```babylemmatizer.py``` command line API. The command line interface is purposefully simple and does not give user direct access to any additional parameters.

```
GENERAL PARAMETERS (use only one)
--build=<arg>                  Builds data from CoNNL-U files in your conllu folder
--train=<arg>                  Trains a model or models from the built data
--build-train=<arg>            Builds data and trains a model or models
--evaluate=<arg>               Evaluates and cross-validates your model or models
--evaluate-fast=<arg>          Rerun evaluation without running POS-tagger and lemmatizer
                               (only post-corrections are applied, useful if you want to tweak the override lexicon
                                or if you just want to quickly see the evaluation results of your model again.
                                You must run --evaluate at least once for you model before using --evaluate-fast)

PATH AND OPTIONS
--use-cpu                      Use CPU instead of GPU (read more below)
--conllu-path=<arg>            Path where to read CoNLL-U files
--model-path=<arg>             Path where to save/read models  
--tokenizer=<arg>              Select input tokenization type when you use --build or --build-train (default = 0)
                               0 : Partly unindexed logo-syllabic tokenization (Akkadian, Elamite, Hittite, Urartian, Hurrian)
                               1 : Indexed logo-syllabic (Sumerian)
                               2 : Character sequences (Non-cuneiform languages, like Greek, Latin, Sanskrit etc.)
```

All these parameters have one mandatory argument, which points to the data in your ```conllu``` folder if you are building new data, or to your ```models``` folder if you are training or evaluating models. For example, if you have CoNLL-U files ```assyrian-train.conllu, assyrian-dev.conllu, assyrian-test.conllu``` and want to build data and train models for them, you can call BabyLemmatizer ```python babylemmatizer.py --build-train=assyrian```. In case you want to train several models for n-fold cross-validation, you can have train/dev/test CoNLL-U files with prefixes followed by numbers, e.g. with n=10 ```assyrian0, assyrian1, ..., assyrian9``` and use the command ```python babylemmatizer.py --build-train=assyrian*```. Similarly, to cross-validate these models after training, use ```python babylemmatizer.py --evaluate=assyrian*```.

Note that ```--tokenizer``` is defined only when you build the model. This does nothing if used with --evaluate or --lemmatize, as the tokenization preferences are saved in your model.

***Using CPU:*** If you want to use CPU instead of GPU (i.e. if you get a CUDA error), use parameter ```--use-cpu``` in addition with parameters ```--train, --build-train``` and ```--evaluate```. Note that training models with CPU is extremely slow and may take days depending on your training data size and hardware. However, you can lemmatize new texts using CPU without too much waiting.

On the first run OpenNMT may take a while to initialize (up to few minutes depending on your system).

# Performance

For 10-fold cross-validated results see Sahala & Lindén (2023). The table below summarizes the performance of the pretrained models. Full lacunae are not counted in the results as labeling them is trivial.

|            | Greek   | Latin   | Sum-L  | Sum-A  | Bab-1st  | Bab-2nd  | Neo-Ass | Mid-Ass | Urartian |
|------------|-------|-------|-------|-------|-------|-------|-------|-------|-------|
| Tagger     | 97.22 | 95.38 | 94.00 | 96.48 | 96.84 | 97.85 | 97.49 | 96.76 | 96.51 |
| Lemmatizer | 97.62 | 96.49 | 93.70 | 95.42 | 95.36 | 94.59 | 95.44 | 94.46 | 93.96 |
| OOV-rate   | 11.03 | 10.58 | 19.04 | 5.44  | 6.63  | 13.04 | 9.51  | 10.21 | 8.26  |

Sum-L = literary, Sum-A = administrative, Bab-1st = first millennium Babylonian, Bab-2nd = second millennium Babylonian.

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
If you use BabyLemmatizer for annotating your data or training new models, please cite the following 2023 paper:

```
@inproceedings{sahala2023babylemmatizer,
  title={A Neural Pipeline for Lemmatizing and POS-tagging Cuneiform Languages},
  author={Sahala, Aleksi and Lindán, Krister},
  booktitle={Proceedings of RANLP 2023},
  year={2023}
}
```
For use-cases of the earlier version of BabyLemmatizer, see [Sahala et al. 2022](https://helda.helsinki.fi/server/api/core/bitstreams/c8df2cf2-28e2-421a-96e4-d677ab9fd80e/content).

# Upcoming features
In order of priority:

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
* [DONE] model versioning
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

# Latest updates
* 2.1 (2023-09-05): ```--tokenizer``` parameter, models now rembember which tokenization to use if it is defined during --build. Models created in version 2.0 will use logo-syllabic tokenization by default, unless you make a file ```config.txt``` in your model directory (the same place where the yaml files are) and type ```tokenizer=2``` on the first line (see command line parameters for possible values).

# Data-openness Disclaimer
This tool was made possible by open data, namely thousands of work-hours invested in annotating Oracc projects. If you use BabyLemmatizer for your dataset, it is HIGHLY advised that your corpus will be shared openly (e.g. CC-BY SA). Sitting on a corpus does not give it the recognition it could have, if it were distributed openly. Just be sure to publish a paper describing your data to ensure academically valued citations.
