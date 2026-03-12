# model.py
import h5py
import json
import tensorflow as tf
from tensorflow.keras.layers import (
    Dense, Dropout, Embedding, GlobalAveragePooling1D,
    Input, Layer, LayerNormalization, MultiHeadAttention
)
from tensorflow.keras.models import Model, Sequential
from agents.expriments.Next_Tool_Recommendation.config import settings

# ------------------- Transformer -------------------
class TransformerBlock(Layer):
    def __init__(self, embed_dim=128, num_heads=4, ff_dim=128, rate=0.1):
        super().__init__()
        self.att = MultiHeadAttention(num_heads=num_heads, key_dim=embed_dim, dropout=rate)
        self.ffn = Sequential([Dense(ff_dim, activation="relu"), Dense(embed_dim)])
        self.layernorm1 = LayerNormalization(epsilon=1e-6)
        self.layernorm2 = LayerNormalization(epsilon=1e-6)
        self.dropout1 = Dropout(rate)
        self.dropout2 = Dropout(rate)

    def call(self, inputs, training=False):
        attn_output, attention_scores = self.att(
            inputs, inputs, inputs, return_attention_scores=True, training=training
        )
        attn_output = self.dropout1(attn_output, training=training)
        out1 = self.layernorm1(inputs + attn_output)
        ffn_output = self.ffn(out1)
        ffn_output = self.dropout2(ffn_output, training=training)
        return self.layernorm2(out1 + ffn_output), attention_scores

class TokenAndPositionEmbedding(Layer):
    def __init__(self, maxlen, vocab_size, embed_dim=128):
        super().__init__()
        self.token_emb = Embedding(input_dim=vocab_size, output_dim=embed_dim, mask_zero=True)
        self.pos_emb = Embedding(input_dim=maxlen, output_dim=embed_dim)

    def call(self, x):
        maxlen = tf.shape(x)[-1]
        positions = tf.range(start=0, limit=maxlen, delta=1)
        positions = self.pos_emb(positions)
        x = self.token_emb(x)
        return x + positions

def build_transformer_model(vocab_size, max_seq_len=settings.MAX_SEQ_LEN):
    inputs = Input(shape=(max_seq_len,))
    x = TokenAndPositionEmbedding(max_seq_len, vocab_size)(inputs)
    x, weights = TransformerBlock()(x)
    x = GlobalAveragePooling1D()(x)
    x = Dropout(0.1)(x)
    x = Dense(128, activation="relu")(x)
    x = Dropout(0.1)(x)
    outputs = Dense(vocab_size, activation="sigmoid")(x)
    return Model(inputs=inputs, outputs=[outputs, weights])

#  Model Manager
class ModelManager:
    def __init__(self, model_path=None):
        self.model = None
        self.reverse_dict = None
        self.model_dict = None
        self.class_weights = None
        self.model_path = model_path or settings.MODEL_PATH  

    def load(self):
        with h5py.File(self.model_path, "r") as f:
            self.reverse_dict = json.loads(f["reverse_dict"][()].decode("utf-8"))
            class_weights = json.loads(f["class_weights"][()].decode("utf-8"))
        self.model_dict = {v: int(k) for k, v in self.reverse_dict.items()}
        self.class_weights = {int(k): v for k, v in class_weights.items()}

        vocab_size = len(self.reverse_dict) + 1
        self.model = build_transformer_model(vocab_size)
        self.model.load_weights(self.model_path)

    @property
    def forward_dict(self):
        return self.model_dict

    def get_model(self):
        return self.model

    def get_metadata(self):
        return self.reverse_dict, self.model_dict, self.class_weights
    
class ModelManager:
    def __init__(self):
        pass

    def load(self):
        pass


# create singleton instance
model_manager = ModelManager()