import sys
sys.path.append('..')
from utils import *

import argparse
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

class KSNNet(nn.Module):
    def __init__(self, game, args):
        # game params
        self.board_x = game.getBoardSize()
        self.action_size = game.getActionSize()
        self.nv = game.getNv()
        self.args = args

        super(KSNNet, self).__init__()

        # Clause:
        # *2 for positive and negative and +1 for clause separator 0
        # self.embeddings = nn.Embedding(self.nv*2+1, self.args.embedding_size) # TODO: Think - not considering the 0 as padding idx

        # Prior actions: # action_size includes 0 
        self.embeddings = nn.Embedding(self.action_size, self.args.embedding_size, padding_idx=0)

        self.fc1 = nn.Linear(self.board_x*self.args.embedding_size, 256)
        self.fc_bn1 = nn.BatchNorm1d(256)

        self.fc2 = nn.Linear(256, 128)
        self.fc_bn2 = nn.BatchNorm1d(128)

        self.fc3 = nn.Linear(128, self.action_size)

        self.fc4 = nn.Linear(128, 1)

    def forward(self, s):

        s = self.embeddings(s) 
        s = torch.reshape(s, (s.shape[0], -1)) # batch_size x (embedding_size * size of the embedding)
        s = F.dropout(F.relu(self.fc_bn1(self.fc1(s))), p=self.args.dropout, training=self.training)  # batch_size x 64
        s = F.dropout(F.relu(self.fc_bn2(self.fc2(s))), p=self.args.dropout, training=self.training)  # batch_size x 32

        pi = self.fc3(s)                                                                         # batch_size x action_size
        v = self.fc4(s)                                                                          # batch_size x 1

        return F.log_softmax(pi, dim=1), torch.tanh(v) # TODO: https://stackoverflow.com/questions/65192475/pytorch-logsoftmax-vs-softmax-for-crossentropyloss
