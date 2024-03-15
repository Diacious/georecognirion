import tensorflow as tf
import random


class PreprocessLayer(tf.keras.layers.Layer):
    def __init__(self, p: float, layers: list, ps=None):
        super().__init__()
        self.p = p
        if ps:
            assert len(layers) == len(ps)
            self.ps = ps
        else:
            self.ps = [0.4] * len(layers)
        self.layers = layers

    def call(self, inputs):
        p = random.uniform(0, 1)
        out = inputs
        if p <= self.p:
            for layer, p_l in zip(self.layers, self.ps):
                if random.uniform(0, 1) <= p_l:
                    out = layer(out)
        return out