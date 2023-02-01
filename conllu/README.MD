# Conll-u files for training the models
The files must be named as follows ```modelname-type.conllu```, where *modelname* is an arbitrary name that describes your model, *type* is either ```train```, ```test``` or ```dev``` depending on the function of your dataset. For example: ```latebabylonian-train.conllu```, ```latebabylonian-dev.conllu``` and ```latebabylonian-test.conllu```. Avoid using any special characters in your model names, except for numbers and underscore.

The standard practice is to use 80% of your training corpus as the train data, and split the remaining 20% into test and dev data.

## Input data format
Input data format must follow Oracc conventions. If you have your transliteration in any other notation, you must convert it into Oracc notation.

## How does Conll-u look like?
See official description of the format at [Universal Dependencies website](https://universaldependencies.org/format.html). In short, it is a word-per-line format closely related to TSV and VRT. Each segment (e.g. line, sentence, text) is separated by an empty line, and each line of text data consists of 10 tab-separated fields: ```ID, FORM, LEMMA, UPOS, XPOS, FEATS, HEAD, DEPREL, DEPS, MISC```. For our purposes ```UPOS``` and ```XPOS``` fields contain the same information, ```FEATS``` is always empty, ```HEAD``` and ```DEPREL``` indicate the first word as the segment as *root* and *0*, and the following words as *child* and *1*, ```DEPS``` field has and *_* and ```MISC``` contains whatever other information.

The important fields are ```FORM``` that contains *transliteration* and ```LEMMA``` that contains the lemma. See example below. Conllu always wnends with and empty line.


```
1	ki-i	kī	PRP	PRP	empty	0	root	_	like
2	iš-ku-nu	šakānu	V	V	empty	1	child	_	put
3	{URU}an-at	Anat	SN	SN	empty	1	child	_	Anat

1	ul-te-šib	wašābu	V	V	empty	0	root	_	sit (down)
2	URU	ālu	N	N	empty	1	child	_	city
3	{URU}an-at	Anat	SN	SN	empty	1	child	_	Anat
4	ki	kī	PRP	PRP	empty	1	child	_	like
5	pa-na-a-ma	pāna	AV	AV	empty	1	child	_	formerly

```
