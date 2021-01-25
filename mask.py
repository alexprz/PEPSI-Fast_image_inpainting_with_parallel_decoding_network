from PIL import Image, ImageDraw


def get_masked_img(img, bbox):
    """Get the original image with a black mask at the given bbox."""
    img = img.copy()
    img_draw = ImageDraw.Draw(img)
    img_draw.rectangle(bbox, fill='black')

    return img


if __name__ == '__main__':
    import os
    from dataset import load_celeba
    from main import Width, Height, mask_size
    os.makedirs('dataset/celeba/masked/images/', exist_ok=True)

    test_paths = load_celeba('small-test')

    for path in test_paths:
        img = Image.open(path)
        img = img.resize((Height, Width))
        x1 = (Width - mask_size)//2
        x2 = (Width + mask_size)//2
        y1 = (Height - mask_size)//2
        y2 = (Height + mask_size)//2
        bbox = (x1, y1, x2, y2)
        masked_img = get_masked_img(img, bbox)

        # masked_img.show()
        basename = os.path.basename(path)
        print(basename)
        masked_img.save(f'dataset/celeba/masked/images/{basename}')
