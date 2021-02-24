import os
import sys
import time

import numpy as np
from tqdm import tqdm

sys.path.append('../../')
from utils import *
from NeuralNet import NeuralNet

import tensorflow as tf
from .JyungoNNet import ResNet as onnet

args = dotdict({
    'lr': 0.001,
    'dropout': 0.3,
    'epochs': 20,
    'batch_size': 1024,
    'num_channels': 64,
})


class NNetWrapper(NeuralNet):
    def __init__(self, game):
        self.nnet = onnet(game, args)
        self.board_x, self.board_y = game.getBoardSize()
        self.action_size = game.getActionSize()
        self.cnt = 0

        self.sess = tf.Session(graph=self.nnet.graph)
        self.saver = None
        with tf.Session() as temp_sess:
            temp_sess.run(tf.global_variables_initializer())
        self.sess.run(tf.variables_initializer(self.nnet.graph.get_collection('variables')))

    def train(self, examples):
        """
        examples: list of examples, each example is of form (board, pi, v)
        """

        for epoch in range(args.epochs):
            print('EPOCH ::: ' + str(epoch + 1))
            pi_losses = AverageMeter()
            v_losses = AverageMeter()
            batch_count = int(len(examples) / args.batch_size)

            # self.sess.run(tf.local_variables_initializer())
            t = tqdm(range(batch_count), desc='Training Net')
            for _ in t:
                sample_ids = np.random.randint(len(examples), size=args.batch_size)
                boards, pis, vs = list(zip(*[examples[i] for i in sample_ids]))
                boards = [np.array(b.regular_stones()) for b in boards]
                # predict and compute gradient and do SGD step
                input_dict = {self.nnet.input_boards: boards, self.nnet.target_pis: pis, self.nnet.target_vs: vs,
                              self.nnet.dropout: args.dropout, self.nnet.isTraining: True}

                # record loss
                self.sess.run(self.nnet.train_step, feed_dict=input_dict)
                pi_loss, v_loss = self.sess.run([self.nnet.loss_pi, self.nnet.loss_v], feed_dict=input_dict)
                pi_losses.update(pi_loss, len(boards))
                v_losses.update(v_loss, len(boards))
                t.set_postfix(Loss_pi=pi_losses, Loss_v=v_losses)

    def predict(self, board):
        """
        board: np array with board
        """
        # timing
        start = time.time()

        # preparing input
        board = np.array(board.regular_stones())[np.newaxis, :, :]

        # run
        prob, v = self.sess.run(
            [self.nnet.prob, self.nnet.v],
            feed_dict={self.nnet.input_boards: board, self.nnet.dropout: 0, self.nnet.isTraining: False}
        )

        # print('PREDICTION TIME TAKEN : {0:03f}'.format(time.time()-start))
        return prob[0], v[0]

    def save_checkpoint(self, folder='checkpoint', filename='checkpoint.pth.tar'):
        filepath = os.path.join(folder, filename)
        if not os.path.exists(folder):
            print("Checkpoint Directory does not exist! Making directory {}".format(folder))
            os.mkdir(folder)
        else:
            print("Checkpoint Directory exists! ")
        if self.saver == None:
            self.saver = tf.train.Saver(self.nnet.graph.get_collection('variables'))
        with self.nnet.graph.as_default():
            self.saver.save(self.sess, filepath)
            # tf.train.write_graph(self.sess.graph_def, folder, f'{filename}.pb', as_text=False)
            # tf.train.write_graph(self.sess.graph_def, folder, f'{filename}.txt', as_text=True)
            #print([node.name for node in self.sess.graph.as_graph_def().node])
        # if filename == 'best.pth.tar':
        #     model_dir='models'
        #     self.cnt += 1
        #     builder = tf.saved_model.builder.SavedModelBuilder(model_dir + '/' + str(self.cnt))
        #     inputs = {
        #         'input_boards': self.nnet.input_boards,
        #         'dropout': self.nnet.dropout,
        #         'is_training': self.nnet.isTraining
        #     }
        #     outputs = {
        #         'prob': self.nnet.prob,
        #         'v': self.nnet.v
        #     }
        #     signature = tf.saved_model.predict_signature_def(inputs=inputs, outputs=outputs)
        #     builder.add_meta_graph_and_variables(sess=self.sess,
        #         tags=[tf.saved_model.tag_constants.SERVING],
        #         signature_def_map={'serving_default': signature})
        #     builder.save()

    def load_checkpoint(self, folder='checkpoint', filename='checkpoint.pth.tar'):
        filepath = os.path.join(folder, filename)
        if not os.path.exists(filepath + '.meta'):
            raise ("No model in path {}".format(filepath))
        with self.nnet.graph.as_default():
            self.saver = tf.train.Saver()
            self.saver.restore(self.sess, filepath)