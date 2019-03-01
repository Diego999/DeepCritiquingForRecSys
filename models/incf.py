import tensorflow as tf
import numpy as np
from tqdm import tqdm
from utils.progress import WorkSplitter, inhour
from scipy.sparse import vstack, hstack


class INCF(object):
    def __init__(self,
                 num_users,
                 num_items,
                 label_dim,
                 text_dim,
                 embed_dim,
                 num_layers,
                 batch_size,
                 lamb=0.01,
                 learning_rate=1e-3,
                 optimizer=tf.train.AdamOptimizer,
                 **unused):
        self.num_users = num_users
        self.num_items = num_items
        self.label_dim = label_dim
        self.text_dim = text_dim
        self.embed_dim = embed_dim
        self.num_layers = num_layers
        self.batch_size = batch_size
        self.lamb = lamb
        self.learning_rate = learning_rate
        self.optimizer = optimizer
        self.get_graph()
        self.sess = tf.Session()
        self.sess.run(tf.global_variables_initializer())

    def get_graph(self):

        self.users_index = tf.placeholder(tf.int32, [None])
        self.items_index = tf.placeholder(tf.int32, [None])
        self.rating = tf.placeholder(tf.int32, [None, self.label_dim])
        self.keyphrase = tf.placeholder(tf.int32, [None, self.text_dim])


        with tf.variable_scope("embeddings"):
            self.user_embeddings = tf.Variable(tf.random_normal([self.num_users, self.embed_dim],
                                                                stddev=1 / (self.embed_dim ** 0.5), dtype=tf.float32))

            self.item_embeddings = tf.Variable(tf.random_normal([self.num_items, self.embed_dim],
                                                                stddev=1 / (self.embed_dim ** 0.5), dtype=tf.float32))

            users = tf.nn.embedding_lookup(self.user_embeddings, self.users_index, name="user_lookup")
            items = tf.nn.embedding_lookup(self.item_embeddings, self.items_index, name="item_lookup")

        with tf.variable_scope("residual"):
            hi = tf.concat((self.item_embeddings, self.user_embeddings), 0)
            for i in range(self.num_layers):
                ho = tf.layers.dense(inputs=hi, units=self.embed_dim, activation=tf.nn.relu)
                hi = tf.concat([hi, ho], axis=0)

        with tf.variable_scope("prediction"):
            rating_prediction = tf.layers.dense(inputs=hi, units=self.label_dim,
                                                activation=None, name='rating_prediction')
            phrase_prediction = tf.layers.dense(inputs=hi, units=self.text_dim,
                                                activation=None, name='phrase_prediction')

        with tf.variable_scope("rating_loss"):
            rating_loss = tf.losses.mean_squared_error(labels=self.rating, predictions=rating_prediction)

        with tf.variable_scope("phrase_loss"):
            phrase_loss = tf.losses.sigmoid_cross_entropy(multi_class_labels=self.keyphrase, logits=phrase_prediction)

        self.loss = (tf.reduce_mean(rating_loss)
                     + tf.reduce_mean(phrase_loss)
                     + tf.losses.get_regularization_loss(self.lamb))

        with tf.variable_scope('optimizer'):
            self.train = self.optimizer(learning_rate=self.learning_rate).minimize(self.loss)


