# CoNLL-U files for training the models
The files **must** be named as follows ```modelname-type.conllu```, where *modelname* is an arbitrary name that describes your model, *type* is either ```train```, ```test``` or ```dev``` depending on the function of your dataset. For example: ```latebabylonian-train.conllu```, ```latebabylonian-dev.conllu``` and ```latebabylonian-test.conllu```. Do not use any special characters in your model names, excluding numbers and underscore.

The standard practice is to use 80% of your training corpus as the train data, and split the remaining 20% into test and dev data.

## Input data format
Input data format must follow [Oracc conventions](http://oracc.museum.upenn.edu/doc/help/languages/akkadian/akkadianstylesheet/index.html). If you have your transliteration in any other notation, you must convert it into Oracc notation.

My library [Cuneiformtools](https://docs.google.com/document/d/1kW9DnCpXGICJ_ttOCO182G2jivE7_knVOZP_v6vdNPw/) may be useful for making transliteration conversions. It is distributed as a part of BabyLemmatizer 2.0 (see [cuneiformtools](https://github.com/asahala/BabyLemmatizer/tree/main/cuneiformtools) folder. You can run the normalization script on your conllu files as follows:

```python babylemmatizer.py --normalize-conllu```

It goes through all conllu files in the ```conllu``` folder and normalize them into ```conllu/normalized```. You can then delete the originals and replace them with normalized files.

Currently BabyLemmatizer does not provide tools for converting ATF to CoNLL-U and backwards, or direct lemmatization of Oracc JSONs, but these features will be added in the future. If you have your text in a unit-per-line format (this unit can be text, sentence or line), you can use the function ```upl_to_conllu()``` in ```conllutools.py``` to add required fields, if you make your own script in the BabyLemmatizer folder, E.g.

```
>>> import conllutools
>>> conllutools.upl_to_conllu('my.txt', 'my.conllu')
```

Will convert a line-per-line text

```
šum-ma a-wi-lum
in DUMU a-wi-lim uh₂-tap-pi-id
in-šu u-ha-ap-pa-du
```

into the following CoNLL-U that can be tagged and lemmatized with BabyLemmatizer:

```
1	šum-ma	_	_	_	_	0	root	_	_
2	a-wi-lum	_	_	_	_	1	child	_	_

1	in	_	_	_	_	0	root	_	_
2	DUMU	_	_	_	_	1	child	_	_
3	a-wi-lim	_	_	_	_	1	child	_	_
4	uh₂-tap-pi-id	_	_	_	_	1	child	_	_

1	in-šu	_	_	_	_	0	root	_	_
2	u-ha-ap-pa-du	_	_	_	_	1	child	_	_

```

If you want to train new models, you need to populate the ```LEMMA, UPOS, XPOS``` fields with lemmatization and pos-tagging. See more information below.


## How does CoNLL-U look like?
See official description of the format at [Universal Dependencies website](https://universaldependencies.org/format.html). In short, it is a word-per-line format closely related to TSV and VRT. Each segment (e.g. line, sentence, text) is separated by an empty line, and each line of text data consists of 10 tab-separated fields: ```ID, FORM, LEMMA, UPOS, XPOS, FEATS, HEAD, DEPREL, DEPS, MISC```. For our purposes ```UPOS``` and ```XPOS``` fields contain the same information, ```FEATS``` is always empty, ```HEAD``` and ```DEPREL``` indicate the first word as the segment as *root* and *0*, and the following words as *child* and *1*, ```DEPS``` field has and *_* and ```MISC``` contains whatever other information.

The important fields are ```FORM``` that contains *transliteration* and ```LEMMA``` that contains the lemma. See example below. **CoNLL-U always ends with and empty line.**


```
1	ki-i	kī	PRP	PRP	_	0	root	_	like
2	iš-ku-nu	šakānu	V	V	_	1	child	_	put
3	{uru}an-at	Anat	SN	SN	_	1	child	_	Anat

1	ul-te-šib	wašābu	V	V	_	0	root	_	sit (down)
2	uru	ālu	N	N	_	1	child	_	city
3	{uru}an-at	Anat	SN	SN	_	1	child	_	Anat
4	ki	kī	PRP	PRP	_	1	child	_	like
5	pa-na-a-ma	pāna	AV	AV	_	1	child	_	formerly

```

## Demo
Extract ```lbtest1.tar.gz``` for some data to test training a model with.
