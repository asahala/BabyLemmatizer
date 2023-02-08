## Network Architecture
Following Kanerva et al. 2021:

```
 NMTModel(
  (encoder): RNNEncoder(
    (embeddings): Embeddings(
      (make_embedding): Sequential(
        (emb_luts): Elementwise(
          (0): Embedding(320, 500, padding_idx=1)
        )
      )
    )
    (rnn): LSTM(500, 250, num_layers=2, batch_first=True, dropout=0.3, bidirectional=True)
  )
  (decoder): InputFeedRNNDecoder(
    (embeddings): Embeddings(
      (make_embedding): Sequential(
        (emb_luts): Elementwise(
          (0): Embedding(32, 500, padding_idx=1)
        )
      )
    )
    (dropout): Dropout(p=0.3, inplace=False)
    (rnn): StackedLSTM(
      (dropout): Dropout(p=0.3, inplace=False)
      (layers): ModuleList(
        (0): LSTMCell(1000, 500)
        (1): LSTMCell(500, 500)
      )
    )
    (attn): GlobalAttention(
      (linear_in): Linear(in_features=500, out_features=500, bias=False)
      (linear_out): Linear(in_features=1000, out_features=500, bias=False)
    )
  )
  (generator): Linear(in_features=500, out_features=32, bias=True)
)

```

## Tagger sequences
Tagger inputs are encoded as 3-grams tokenized into signs: logograms are represented as indexed tokens and syllabograms as unindexed character sequences.

Original: ```ZU₂.LUM.MA {lu₂}mu-kin-ni {m}{d}AG-URU₃-šu₂```

Tagger input: ```ZU₂ . LUM . MA << {LU₂} m u - k i n - n i >> {m} {d} AG - URU₃ - š u```

Tagger output: ```N```

## Lemmatizer sequences (token-based)
Lemmatizer inputs are encoded as single word forms tokenized as above, with adjacent POS tags for context disambiguation.

Original: ```ZU₂.LUM.MA {lu₂}mu-kin-ni {m}{d}AG-URU₃-šu₂```

Lemmatizer input: ```{LU₂} m u - k i n - n i PREV=N UPOS=N NEXT=PN```

Lemmatizer output: ```mukinnu```

