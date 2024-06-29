import numpy as np
import random
import torch
import torch.utils.data
from torch import optim
from torch.nn import functional as F
import sys
import copy

from datasets import MNIST, EMNIST, FashionMNIST, TreesDatasetV1, TreesDatasetV2

from torchvision.utils import save_image


class Trainer(object):
    def __init__(self, args, model):
        self.args = args
        self.device = args.device
        self._init_dataset()

        # Get loaders
        self.train_loader = self.data.train_loader
        self.test_loader = self.data.test_loader

        self.model = model
        self.model.to(self.device)
        if args.dataset in ['MNIST', 'EMNIST', 'FashionMNIST']:
            self.optimizer = optim.Adam(self.model.parameters(), lr=1e-3)
        else:
            self.optimizer = optim.Adadelta(self.model.parameters())
            # self.optimizer = optim.Adam(self.model.parameters(), lr=1e-3)

    def _init_dataset(self):
        if self.args.dataset == 'MNIST':
            self.data = MNIST(self.args)
        elif self.args.dataset == 'EMNIST':
            self.data = EMNIST(self.args)
        elif self.args.dataset == 'FashionMNIST':
            self.data = FashionMNIST(self.args)
        # Custom Dataset
        elif self.args.dataset == 'TreesV1':
            self.data = TreesDatasetV1(self.args)
        elif self.args.dataset == 'TreesV2':
            self.data = TreesDatasetV2(self.args)
        else:
            print("Dataset not supported")
            sys.exit()

    def loss_function(self, recon_x, x, args):
        if args.dataset in ['MNIST', 'EMNIST', 'FashionMNIST']:
            LOSS = F.binary_cross_entropy(recon_x, x.view(-1, 28 * 28), reduction='sum')
        elif args.dataset == 'TreesV2':
            LOSS = (
                0.5 * F.binary_cross_entropy(recon_x, x.view(-1, 28 * 28), reduction='sum') +
                0.5 * F.l1_loss(recon_x, x.view(-1, 28 * 28), reduction='sum')
            )
        else:
            LOSS = F.mse_loss(recon_x, x.view(-1, 64 * 64))
            # LOSS = (
            #     0.5 * F.mse_loss(recon_x, x.view(-1, 64 * 64)) +
            #     0.5 * F.l1_loss(recon_x, x.view(-1, 64 * 64), reduction='sum')
            # )

            # TODO: MIOU, Total Variation, SSIM, F1, EMD
        return LOSS

    def zero_out_radius(self, tensor, point, radius):
        x, y = point[1], point[2]  # Get the coordinates
        for i in range(max(0, x - radius), min(tensor.size(1), x + radius + 1)):
            for j in range(max(0, y - radius), min(tensor.size(2), y + radius + 1)):
                if (i - x) ** 2 + (j - y) ** 2 <= radius ** 2:
                    tensor[0, i, j] = 0

    def create_holes(self, target_data):
        for idx in range(len(target_data)):
            white_points = torch.nonzero(target_data[idx] > 0.6)

            if white_points.size(0) > 0:
                # Randomly select one of the non-zero points
                random_point = random.choice(white_points)
                radius = random.randint(3, 5)
                self.zero_out_radius(target_data[idx], random_point, radius)

                # plt.imshow(target_data[idx].permute(1, 2, 0))
                # save_image(target_data[idx], 'img1.png')

    def apply_threshold(self, tensor, threshold):
        tensor[tensor >= threshold] = 1.0
        tensor[tensor < threshold] = 0.0

    # TODO: In the future, use the input data to create the target data with holes (and use only 1 dataloader)
    def _train(self, epoch):
        self.model.train()
        train_loss = 0
        for batch_idx, (input_data, target_data) in enumerate(self.train_loader):
            input_data = input_data.to(self.device)
            if self.args.dataset != 'TreesV1':
                target_data = input_data.clone()
            target_data = target_data.to(self.device)

            # TODO: Threshold
            # self.apply_threshold(input_data, 0.5)
            # self.apply_threshold(target_data, 0.5)

            # Fix for Trees dataset - Fixed problem
            # if input_data.dtype != torch.float32:
            #     input_data = input_data.float()
            # if target_data.dtype != torch.float32:
            #     target_data = target_data.float()

            # # For Equality Check
            # res = torch.eq(input_data, target_data)
            # print(res.max())
            # print(res.min())

            if self.args.dataset != 'TreesV1':
                self.create_holes(input_data)

            # # For Equality Check
            # res = torch.eq(input_data, target_data)
            # print(res.max())
            # print(res.min())

            self.optimizer.zero_grad()
            recon_batch = self.model(input_data)
            loss = self.loss_function(recon_batch, target_data, self.args)
            loss.backward()

            train_loss += loss.item()
            self.optimizer.step()
            if batch_idx % self.args.log_interval == 0:
                print('Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}'.format(
                    epoch, batch_idx * len(input_data), len(self.train_loader.dataset),
                    100. * batch_idx / len(self.train_loader),
                    loss.item() / len(input_data)))

        print('====> Epoch: {} Average loss: {:.4f}'.format(
              epoch, train_loss / len(self.train_loader.dataset)))

    def _test(self):
        self.model.eval()
        test_loss = 0
        with torch.no_grad():
            for i, (input_data, target_data) in enumerate(self.test_loader):
                input_data = input_data.to(self.device)
                if self.args.dataset != 'TreesV1':
                    target_data = input_data.clone()
                target_data = target_data.to(self.device)

                # TODO: Threshold
                # self.apply_threshold(input_data, 0.5)
                # self.apply_threshold(target_data, 0.5)

                if input_data.dtype != torch.float32:
                    input_data = input_data.float()
                if target_data.dtype != torch.float32:
                    target_data = target_data.float()

                if self.args.dataset != 'TreesV1':
                    self.create_holes(input_data)

                recon_batch = self.model(input_data)
                test_loss += self.loss_function(recon_batch, target_data, self.args).item()

        test_loss /= len(self.test_loader.dataset)
        print('====> Test set loss: {:.4f}'.format(test_loss))

    def train(self):
        try:
            for epoch in range(1, self.args.epochs + 1):
                self._train(epoch)
                self._test()
        except (KeyboardInterrupt, SystemExit):
            print("Manual Interruption")

        print("Saving Model Weights")
        model_parameters = copy.deepcopy(self.model.state_dict())
        torch.save(model_parameters, self.args.weights_filepath)
