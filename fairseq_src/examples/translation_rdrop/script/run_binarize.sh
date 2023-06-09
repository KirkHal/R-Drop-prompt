#!/usr/bin/env bash

#TEXT=examples/translation_rdrop/iwslt14.tokenized.de-en
#fairseq-preprocess --source-lang de --target-lang en \
#    --joined-dictionary \
#    --trainpref $TEXT/train --validpref $TEXT/valid --testpref $TEXT/test \
#    --destdir data-bin/iwslt14.rdrop.tokenized.de-en \
#    --workers 20

TEXT=examples/translation_rdrop/iwslt14.tokenized.de-en
fairseq-preprocess --source-lang de_pmt --target-lang en_pos \
    --joined-dictionary \
    --trainpref $TEXT/train --validpref $TEXT/valid --testpref $TEXT/test \
    --destdir data-bin/iwslt14.prompt.tokenized.de-en \
    --workers 20
