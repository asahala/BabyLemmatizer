def write_yaml(filename, content):
    with open(filename, 'w') as f:
        f.write(content)
    
def make_lemmatizer_yaml(prefix, MODEL_PATH):
    lemmatizer =\
f"""save_data: models/{prefix}/lemmatizer/model
src_vocab: models/{prefix}/lemmatizer/vocab.src
tgt_vocab: models/{prefix}/lemmatizer/vocab.tgt
overwrite: True

# Corpus opts:
data:
    corpus_1:
        path_src: models/{prefix}/lemmatizer/traindata/train.src
        path_tgt: models/{prefix}/lemmatizer/traindata/train.tgt
    valid:
        path_src: models/{prefix}/lemmatizer/traindata/dev.src
        path_tgt: models/{prefix}/lemmatizer/traindata/dev.tgt

# Vocabulary files that were just created
#src_vocab: models/{prefix}/lemmatizer/vocab.src
#tgt_vocab: models/{prefix}/lemmatizer/vocab.tgt

# Train on a single GPU
world_size: 1
gpu_ranks: [0]

#####

# Where to save the checkpoints
save_model: models/{prefix}/lemmatizer/model
save_checkpoint_steps: 35000
train_steps: 35000
valid_steps: 15000

dropout: 0.3
optim: adam
learning_rate: 0.0005
learning_rate_decay: 0.9
encoder_type: brnn
batch_size: 64
start_decay_steps: 15000
decay_steps: 512"""

    write_yaml(MODEL_PATH + 'lemmatizer.yaml', lemmatizer)

def make_tagger_yaml(prefix, MODEL_PATH):
    tagger =\
f"""save_data: models/{prefix}/tagger/model
src_vocab: models/{prefix}/tagger/vocab.src
tgt_vocab: models/{prefix}/tagger/vocab.tgt
overwrite: True

# Corpus opts:
data:
    corpus_1:
        path_src: models/{prefix}/tagger/traindata/train.src
        path_tgt: models/{prefix}/tagger/traindata/train.tgt
    valid:
        path_src: models/{prefix}/tagger/traindata/dev.src
        path_tgt: models/{prefix}/tagger/traindata/dev.tgt

# Vocabulary files that were just created
#src_vocab: models/{prefix}/tagger/vocab.src
#tgt_vocab: models/{prefix}/tagger/vocab.tgt

# Train on a single GPU
world_size: 1
gpu_ranks: [0]

#####

# Where to save the checkpoints
save_model: models/{prefix}/tagger/model
save_checkpoint_steps: 35000
train_steps: 35000
valid_steps: 15000

dropout: 0.3
optim: adam
learning_rate: 0.0005
learning_rate_decay: 0.9
encoder_type: brnn
batch_size: 64
start_decay_steps: 15000
decay_steps: 512"""

    write_yaml(MODEL_PATH + 'tagger.yaml', tagger)
