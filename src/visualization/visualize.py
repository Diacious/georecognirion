import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import click
import os


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


@click.command()
@click.argument('data_path', type=click.Path(exists=True))
def main(data_path):
    dir_paths = list(os.walk(data_path))
    class_names = sorted(dir_paths[0][1])
    images_paths = sorted(dir_paths[1:], key=lambda x: x[0])

    label_mapping = get_labels(class_names, images_paths)

    # Visualization of class distribution
    labels_df = pd.DataFrame([label for label in label_mapping if label != -1], columns=['labels'])
    plt.figure(figsize=(20, 10))
    sns.countplot(data=labels_df, x='labels')
    plt.show()


if __name__ == '__main__':
    main()