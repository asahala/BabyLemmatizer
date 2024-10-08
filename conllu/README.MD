# Input data format
Input data format must follow [Oracc conventions](http://oracc.museum.upenn.edu/doc/help/languages/akkadian/akkadianstylesheet/index.html). If you have your transliteration in any other notation, you must convert it into Oracc notation. BabyLemmatizer automatically normalizes transliterations to a certain extent:

1. Accented and numeric indexation is converted into subscripts.
2. Brackets, question marks etc. indicating lacunae are removed.
3. Determinatives are lowercased as long as they are wrapped between curly brackets.
4. Character ḫ is normalized into h.

My library [Cuneiformtools](https://docs.google.com/document/d/1kW9DnCpXGICJ_ttOCO182G2jivE7_knVOZP_v6vdNPw/) may be useful for making transliteration conversions. It is distributed as a part of BabyLemmatizer 2.0 (see [cuneiformtools](https://github.com/asahala/BabyLemmatizer/tree/main/cuneiformtools) folder.

### Rawtext to CoNLL-U+
You can use the script ```txt2conllu.py --filename=yourpath/yourfile.txt``` to convert line-per-line raw text format into CoNLL-U+. For example,

```
# Code of Hammurapi example
šum-ma a-wi-lum
in DUMU a-wi-lim úh-tap-pi-id
in-šu u-ha-ap-pa-du
```

into the following CoNLL-U that can be tagged and lemmatized with BabyLemmatizer:

```
# Code of Hammurapi example
1	šum-ma	_	_	_	_	0	root	_	_ ...
2	a-wi-lum	_	_	_	_	1	child	_	_ ...

1	in	_	_	_	_	0	root	_	_ ...
2	DUMU	_	_	_	_	1	child	_	_ ...
3	a-wi-lim	_	_	_	_	1	child	_	_ ...
4	uh₂-tap-pi-id	_	_	_	_	1	child	_	_ ...

1	in-šu	_	_	_	_	0	root	_	_ ...
2	u-ha-ap-pa-du	_	_	_	_	1	child	_	_ ...

```

If you want to train new models, you need to populate the ```LEMMA``` and ```XPOS``` fields with lemmatization and pos-tagging. See more information below.


# BabyLemmatizer CoNLL-U+ file format description
CoNLL-U is a standardized format used by the Universal Dependencies [Universal Dependencies website](https://universaldependencies.org/format.html). In short, it is a word-per-line format closely related to TSV (Tab Separated Columns) and VRT (VeRticalized Text). BabyLemmatizer uses an extended CoNLL-U format known as CoNLL-U+. Each segment (e.g. line, sentence, text, whichever you prefer) is separated by an empty line, and each line of text data consists of 10 tab-separated standard CoNLL-U fields: ```ID, FORM, LEMMA, UPOS, XPOS, FEATS, HEAD, DEPREL, DEPS, MISC``` and seven additional fields for extra information ```ENG, NORM, LANG, FORMCTX, XPOSCTX, SCORE, LOCK```. The fields are explained in the table below. The most important fields have been bolded.

Crucial fields are ```FORM``` that contains *transliteration* and ```LEMMA``` that contains the lemma. **Note that CoNLL-U always ends with and empty line.**

| Field | Description |
| --- | --- |
| **ID** | Number of the word in the unit starting from 1 |
| **FORM** | Transliteration |
| **LEMMA** | Lemma (dictionary form) of the word |
| UPOS | UD Part-of-speech tag, for now always underscore _ |
| **XPOS** | Oracc part-of-speech tag. ***NOTE that if you are using UD corpora, the models predict what's in the XPOS field only, now what's in the UPOS!*** This will be changed in the future in a way that he model will predict both, UPOS and XPOS. |
| FEATS | Morphological feats, for now always underscore _ |
| HEAD | Dependency stuff, 0 for the first word of the unit, otherwise 1 |
| DEPREL | Dependency stuff, root for the first word of the unit, otherwise child |
| DEPS | Always underscore _ |
| MISC | Arbitrary information |
| ENG | English translation of the word if available |
| NORM | Normalization (phonological transcription of the word) if available |
| LANG | Word's language, for now always underscore _ |
| FORMCTX | Word's context, filled automatically |
| XPOSCTX | Word's part-of-speech context, filled automatically |
| **SCORE** | Confidence score of the lemmatization: 0.0 OOV logogram, 1.0 OOV logo-syllabic, 2.0 OOV syllabi, 3.0 ambiguous, 4.0 close-to-unambiguous, 5.0 close-to-unambiguous and exists in a previously known context. |
| **LOCK** | [DISABLED AS OF AUGUST 2024 DUE TO A BUG! DO NOT USE, ALWAYS USE _ IN THIS FIELD OR THE SYSTEM WILL NOT WORK] |

# CoNLL-U+ files for training models
The files **must** be named as follows ```modelname-type.conllu```, where *modelname* is an arbitrary name that describes your model, *type* is either ```train```, ```test``` or ```dev``` depending on the function of your dataset. For example: ```latebabylonian-train.conllu```, ```latebabylonian-dev.conllu``` and ```latebabylonian-test.conllu```. Do not use any special characters in your model names, excluding numbers and underscore.

Your files must have their ```FORM```, ```LEMMA``` and ```XPOS``` fields populated with Oracc compliant transliteration, lemma and part-of-speech tag. For example, for ```šarru[king]N``` the ```LEMMA``` would be ```šarru``` and ```XPOS``` would be ```N```.  

The standard practice is to use 80% of your training corpus as the train data, and split the remaining 20% into test and dev data. You can create n-fold splits from a single CoNLL-U+ file for training models by using the ```split_training_data()``` method in  ```conllutools.py```.  For example ```conllutools.split_training_data(source='mypath/source.conllu', n=10)``` splits the data into 80/10/10 train/dev/test sets and saves them into the same folder.

## Demo
Extract ```lbtest1.tar.gz``` for some data to test training a model with.

# Bringing annotations back to the original format
This remains user's responsibility. Currently BabyLemmatizer does not provide tools for converting CoNLL-U+ into ATF, Oracc JSON etc.
