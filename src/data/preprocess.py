import click
import logging
import os
import imghdr
import shutil
from pathlib import Path
from dotenv import find_dotenv, load_dotenv
from struct import unpack
from PIL import Image

marker_mapping = {
    0xffd8: "Start of Image",
    0xffe0: "Application Default Header",
    0xffdb: "Quantization Table",
    0xffc0: "Start of Frame",
    0xffc4: "Define Huffman Table",
    0xffda: "Start of Scan",
    0xffd9: "End of Image"
}


class JPEG:
    def __init__(self, image_file):
        with open(image_file, 'rb') as f:
            self.img_data = f.read()

    def decode(self):
        data = self.img_data
        while(True):
            marker, = unpack(">H", data[0:2])
            if marker == 0xffd8:
                data = data[2:]
            elif marker == 0xffd9:
                return
            elif marker == 0xffda:
                data = data[-2:]
            else:
                lenchunk, = unpack(">H", data[2:4])
                data = data[2+lenchunk:]
            if len(data)==0:
                break


def del_corrupted_files(images_paths, output_dir):
    img_type_accepted_by_tf = ["bmp", "gif", "jpeg", "png", "jpg"]
    for images in images_paths:
        for im in images[-1]:
            filepath = images[0] + '/' + im

            dir_path = images[0].split('\\')[-2: ]
            dst = Path(f'{output_dir}/{dir_path[0]}')

            if not dst.exists():
                dst.mkdir()

            dst= Path(f'{dst}/{dir_path[-1]}')

            if not dst.exists():
                dst.mkdir()
                
            dst = Path(f"{dst}/{im}")

            img_type = imghdr.what(filepath)
            image = Image.open(filepath)

            if image is not None:
                # Get the number of channels
                num_channels = len(image.mode)  # The third dimension of the shape represents channels
                if num_channels < 3:
                    print("Number of Channels:", num_channels)
                    #os.remove(filepath)
                    continue
            else:
                print("Image not found or unable to open.")

            img= JPEG(filepath)
            try:
                img.decode()
            except:
                #os.remove(filepath)
                continue

            try:
                image.verify()
            except:
                print(f'corrupted file: {filepath}')
                #os.remove(filepath)
                continue

            if img_type is None:
                #os.remove(filepath)
                print(f"{filepath} is not an image")
                continue
            elif img_type not in img_type_accepted_by_tf:
                #os.remove(filepath)
                print(f"{filepath} is a {img_type}, not accepted by TensorFlow")
                continue
            shutil.copyfile(filepath, dst)


@click.command()
@click.argument('input_filepath', type=click.Path(exists=True))
@click.argument('output_filepath', type=click.Path())
def main(input_filepath, output_filepath):
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).
    """
    dirname = os.path.dirname(__file__).split('\\')

    dir_paths = list(os.walk(input_filepath))
    class_names = sorted(dir_paths[0][1])
    images_paths = sorted(dir_paths[1:], key=lambda x: x[0])

    del_corrupted_files(images_paths, output_filepath)

    logger = logging.getLogger(__name__)
    logger.info('making final data set from raw data')


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()