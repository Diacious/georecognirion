import tensorflow as tf
import tensorflow_hub as hub
import click
import os
import numpy as np
from urllib.parse import unquote_plus

tf.compat.v1.enable_resource_variables()
module = hub.KerasLayer("https://tfhub.dev/google/bit/m-r101x1/1")

mapping_to_category = {}
landmarks_info = {}

dirname = os.path.dirname(__file__).split('\\')[:-2]
PATH = '/'.join(dirname)

# File which contains landmarks and their corresponded labels
with open(f'{PATH}/landmarks_labels.csv', encoding='utf-8') as f:
    for line in f:
        label, landmark = line.strip().split(';')
        mapping_to_category[int(label)] = landmark

# File which contains infromation abou landmarks 
with open(f'{PATH}/landmarks_info.csv', encoding='utf-8') as f:
    for line in f:
        landmark, desc = line.strip().split(';')
        landmarks_info[landmark] = desc


# Getting infromation about landmark
def get_landmark_info(model, path) -> str:
    image_path = unquote_plus(path) #"/media/tmp/3_7.jpg"

    img = tf.keras.utils.load_img(image_path)
    img = img.resize((321, 321))
    input_arr = tf.keras.utils.img_to_array(img)
    input_arr = np.array([input_arr])

    pred = int(tf.argmax(tf.squeeze(model(input_arr, 0))))

    pred_landmark = mapping_to_category[pred]
    desc = landmarks_info[pred_landmark].replace('\\n', '\n')
    return pred_landmark.replace('_', ' '), desc


@click.command()
@click.argument('model_path', type=click.Path(exists=True))
@click.argument('image_path', type=click.Path())
def main(model_path, image_path):
    model = tf.keras.models.load_model(model_path, custom_objects={'KerasLayer': module})

    pred_landmark, desc = get_landmark_info(model, image_path)

    print(pred_landmark, '\n')
    print(desc)


if __name__ == '__main__':
    main()
