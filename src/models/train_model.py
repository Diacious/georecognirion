from ..features.build_features import PreprocessLayer
import tensorflow as tf
import tensorflow_hub as hub
import click
import os

tf.compat.v1.enable_resource_variables()
module = hub.KerasLayer("https://tfhub.dev/google/bit/m-r101x1/1")
layers = [
        tf.keras.layers.RandomZoom((-0.4, 0), (-0.4, 0)),
        tf.keras.layers.RandomRotation(1, fill_mode='reflect',),
        tf.keras.layers.RandomContrast(0.6,),
        tf.keras.layers.RandomBrightness(0.5,)
]

def get_labels(class_names, images_paths):
        label_mapping = []
        prev_index = -1
        curr_index = 0
        mapping_to_category = {}

        for category, images in zip(class_names, images_paths):
                curr_index = prev_index + 1
                prev_index += 1
                for im in images[-1]:
                        if not mapping_to_category.get(curr_index, None) and curr_index != -1:
                                mapping_to_category[curr_index] = category
                        label_mapping.append(curr_index)
        return label_mapping


# Model creation
def create_model(num_classes, lr):
        inputs = tf.keras.Input((321, 321, 3))
        alignment = PreprocessLayer(0.1, layers)(inputs)
        processed = tf.keras.layers.Rescaling(1./255)(inputs)
        hidden = module(processed)
        relu = tf.keras.layers.ReLU()(hidden)
        fc_1 = tf.keras.layers.Dense(512, activation='relu')(relu)
        drop_fc_1 = tf.keras.layers.Dropout(0.2)(fc_1)
        output_1 = tf.keras.layers.Dense(num_classes, activation='softmax', use_bias=False)(drop_fc_1)

        model = tf.keras.Model(inputs=inputs, outputs=[output_1])

        model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=lr),
                loss=tf.keras.losses.CategoricalFocalCrossentropy(),
                metrics=['accuracy', tf.keras.metrics.F1Score(), tf.keras.metrics.Precision(), tf.keras.metrics.Recall()])
        
        return model


def fit_model(model, data, n_epoch, output_dir):
        # Callback for early saving model
        check = tf.keras.callbacks.ModelCheckpoint(
                output_dir + '/{epoch:02d}_{loss:.2f}.hdf5',
                monitor='loss',
        )

        model.fit(data, epochs=n_epoch, callbacks=[check])

        return model


@click.command()
@click.argument('input_filepath', type=click.Path(exists=True))
@click.argument('output_filepath', type=click.Path())
@click.argument('batch_size', type=click.INT)
@click.argument('n_epoch', type=click.INT)
@click.argument('lr', type=click.FLOAT)
def main(input_filepath, output_filepath, batch_size, n_epoch, lr):
        '''
        - input_filepath - path to the data\n
        - output_filepath - path to the directroy where to save model
        '''
        img_height = 321
        img_width = 321

        dir_paths = list(os.walk(input_filepath))
        class_names = sorted(dir_paths[0][1])
        images_paths = sorted(dir_paths[1:], key=lambda x: x[0])

        label_mapping = get_labels(class_names, images_paths)
        model = create_model(len(class_names), lr)

        train_ds = tf.keras.utils.image_dataset_from_directory(
                input_filepath,
                label_mapping,
                #subset="training",
                seed=123,
                image_size=(img_height, img_width),
                batch_size=batch_size).map(lambda x, y: (x, tf.one_hot(y, len(class_names))))
        
        model = fit_model(model, train_ds, n_epoch, output_filepath)


if __name__ == '__main__':
    main()

