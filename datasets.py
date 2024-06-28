import torch
from torchvision import datasets, transforms
import os

from tools.dataset_and_dataloaders import TreesCustomDataloader


class MNIST(object):
    def __init__(self, args):
        kwargs = {'num_workers': 1, 'pin_memory': True} if args.cuda else {}
        self.train_loader = torch.utils.data.DataLoader(
            datasets.MNIST('data/mnist', train=True, download=True, transform=transforms.ToTensor()),
            batch_size=args.batch_size, shuffle=False, **kwargs)
        self.test_loader = torch.utils.data.DataLoader(
            datasets.MNIST('data/mnist', train=False, transform=transforms.ToTensor()),
            batch_size=args.batch_size, shuffle=False, **kwargs)


class EMNIST(object):
    def __init__(self, args):
        kwargs = {'num_workers': 1, 'pin_memory': True} if args.cuda else {}
        self.train_loader = torch.utils.data.DataLoader(
            datasets.EMNIST('data/emnist', train=True, download=True, split='byclass', transform=transforms.ToTensor()),
            batch_size=args.batch_size, shuffle=False, **kwargs)
        self.test_loader = torch.utils.data.DataLoader(
            datasets.EMNIST('data/emnist', train=False, split='byclass', transform=transforms.ToTensor()),
            batch_size=args.batch_size, shuffle=False, **kwargs)


class FashionMNIST(object):
    def __init__(self, args):
        kwargs = {'num_workers': 1, 'pin_memory': True} if args.cuda else {}
        self.train_loader = torch.utils.data.DataLoader(
            datasets.FashionMNIST('data/fmnist', train=True, download=True, transform=transforms.ToTensor()),
            batch_size=args.batch_size, shuffle=False, **kwargs)
        self.test_loader = torch.utils.data.DataLoader(
            datasets.FashionMNIST('data/fmnist', train=False, transform=transforms.ToTensor()),
            batch_size=args.batch_size, shuffle=False, **kwargs)


# Custom Dataset
class TreesDatasetV1(object):
    def __init__(self, args):
        # Option 1
        # src_path = os.path.join(str(os.path.dirname(__file__)), "tools", "cropped_src_images")
        # dst_path = os.path.join(str(os.path.dirname(__file__)), "tools", "cropped_dst_images")

        # Option 2
        # src_path = os.path.join(str(os.path.dirname(__file__)), "tools", "parse_preds_mini_cropped")
        # dst_path = os.path.join(str(os.path.dirname(__file__)), "tools", "parse_labels_mini_cropped")

        # Option 3
        src_path = os.path.join(str(os.path.dirname(__file__)), "tools", "parse_preds_mini_cropped_v2")
        dst_path = os.path.join(str(os.path.dirname(__file__)), "tools", "parse_labels_mini_cropped_v2")

        data_paths = [src_path, dst_path]
        trees_dataloader = TreesCustomDataloader(data_paths=data_paths, args=args)
        self.train_loader, self.test_loader = trees_dataloader.get_dataloader()


class TreesDatasetV2(object):
    def __init__(self, args):
        src_path = os.path.join(str(os.path.dirname(__file__)), "tools", "mini_cropped_images")
        data_paths = [src_path]

        trees_dataloader = TreesCustomDataloader(data_paths=data_paths, args=args)
        self.train_loader, self.test_loader = trees_dataloader.get_dataloader()
