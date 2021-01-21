"""Download and prepare the CelebA dataset."""
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder


# celeba = datasets.CelebA('dataset/', download=False)


# train_imgfolder = ImageFolder('dataset/celeba/train')
# test_imgfolder = ImageFolder('dataset/celeba/test')

# print(list(train_imgfolder.__dict__.keys()))
# print(train_imgfolder.imgs)
# print(test_imgfolder)

# train_paths = [k[0] for k in train_imgfolder.imgs]
# test_paths = [k[0] for k in test_imgfolder.imgs]

# print(train_paths)
# print(test_paths)


def load_celeba(which):
    assert which in ['train', 'test']

    if which == 'train':
        train_imgfolder = ImageFolder('dataset/celeba/train')
        train_paths = [k[0] for k in train_imgfolder.imgs]

        return train_paths

    if which == 'test':
        test_imgfolder = ImageFolder('dataset/celeba/test')
        test_paths = [k[0] for k in test_imgfolder.imgs]

        return test_paths


paths = load_celeba('test')
print(len(paths))
