def write_yaml(filename, content):
    with open(filename, 'w') as f:
        f.write(content)

def set_hyper(examples, steps_per_epoch,
              total_steps, start_decay):

    decay_steps = int(steps_per_epoch/10)

    return f"""save_checkpoint_steps: {total_steps}
train_steps: {total_steps}
valid_steps: {steps_per_epoch}

dropout: 0.3
optim: adam
learning_rate: 0.0005
learning_rate_decay: 0.9
encoder_type: brnn
batch_size: 64
start_decay_steps: {start_decay}
decay_steps: {decay_steps}"""
    

def make_lemmatizer_yaml(prefix, MODEL_PATH, hyper):
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
{hyper}
"""

    write_yaml(MODEL_PATH + 'lemmatizer.yaml', lemmatizer)

def make_tagger_yaml(prefix, MODEL_PATH, hyper):
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
{hyper}
"""

    write_yaml(MODEL_PATH + 'tagger.yaml', tagger)

"""
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
decay_steps: 512
"""
