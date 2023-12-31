from torch.utils.data import DataLoader
import custom_datasets
import models
from params import *
import training
import os
import numpy as np
import torch
import seaborn as sns
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS
import pandas as pd
from transformers import BertTokenizer

# TASK SHEET: load_data


def load_data(dataset: str, transformation=None, n_train: int = None, n_test: int = None, batch_size=BATCH_SIZE, shuffle=True):  # transformation callable
    """
    TASK SHEET: Function to load dataset in path indicated by name, specify number of training and testing samples, apply transformations and return dataloader.

    Args:
        dataset (str): name of dataset
        transformation (callable): transformation to apply to the data (default: None)
        att_head_dim (int): dimension of each attention head
        n_train (int): number of training samples (default: None)
        n_test (int): number of testing samples (default: None)

    Returns:
        Tuple[torch.utils.data.DataLoader]: training and testing dataloader
    """
    if dataset == "jigsaw_toxicity_pred":
        train = custom_datasets.ToxicComment(
            tokenizer=transformation,
            seq_len=SEQ_LEN,
            split="train",
            n_rows=n_train
        )

        test = custom_datasets.ToxicComment(
            tokenizer=transformation,
            seq_len=SEQ_LEN,
            split="test",
            n_rows=n_test
        )

        # initialize dataloader for training and testing
        train = DataLoader(train, batch_size, shuffle)
        test = DataLoader(test, batch_size, shuffle)
        return train, test

    else:
        raise NotImplementedError("Dataset not implemented")


def generate_wordcloud(text, Title, max_words=20):
    wordcloud = WordCloud(width=800, height=400, max_words=max_words, stopwords=set(
        STOPWORDS), background_color='white').generate(text)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    plt.title(Title)


def tokenize_text(text, tokenizer):
    tokens = tokenizer.encode(text, add_special_tokens=False)
    return len(tokens)

# TASK SHEET: show
def show(csv_path, output_folder=None, graph_name=None):
    """
    Generate and display various graphs based on the specified graph_name using data from a CSV file.

    Args:
    - csv_path (str): The file path of the CSV file containing the data
    - output_folder (str, optional): If provided, the generated graphs will be saved in this folder
    - graph_name (str, optional): The name of the graph to generate, possible values:
        - 'dstr_toxic': Distribution of toxic label occurrences
        - 'wrdcloud_clean': Word cloud for non-toxic comments
        - 'wrdcloud_toxic': Word cloud for toxic comments
        - 'length_per_label': Average comment length for each label
        - 'dstr_length': Distribution of comment lengths
        - 'token_length_per_label': Average token length for each label
        - 'token_length_distribution': Distribution of token lengths for the entire dataset

    Returns:
    - None: Displays the generated graph or saves it in the specified output_folder.

    Example usage:
    ```python
    show('train.csv', graph_name="dstr_toxic")  # Plots without saving
    show('train.csv', output_folder='output_folder', graph_name="dstr_toxic")  # Plots and saves in 'output_folder'
    ```
    """
    df = pd.read_csv(csv_path)
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

    # Graph 1
    if graph_name == 'dstr_toxic':
        label_counts_total = df[ORDER_LABELS].sum().sort_values().values

        plt.figure(figsize=(10, 5))
        ax = sns.barplot(x=label_counts_total,
                         y=ORDER_LABELS, palette='viridis')

        for i, v in enumerate(label_counts_total):
            ax.text(v + 0.5, i, str(v), color='black', ha='left', va='center')

        plt.xlabel('Number of Occurrences')
        plt.ylabel('Labels')
        plt.title('Distribution of Toxic Label Occurrences')

    # Graph 2
    elif graph_name == 'wrdcloud_clean':
        non_toxic_text = " ".join(
            df[df[ORDER_LABELS].sum(axis=1) == 0]['comment_text'])
        generate_wordcloud(non_toxic_text, "Word Cloud for Non-Toxic Comments")

    # Graph 3
    elif graph_name == 'wrdcloud_toxic':
        toxic_text = " ".join(
            df[df[ORDER_LABELS].sum(axis=1) > 0]['comment_text'])
        generate_wordcloud(toxic_text, "Word Cloud for Toxic Comments")

    # Graph 4
    elif graph_name == 'length_per_label':
        label_lengths = {label: [] for label in ORDER_LABELS}
        clean_lengths = []

        for i, label in enumerate(ORDER_LABELS):
            label_indices = df[df[label] == 1].index
            label_lengths[label].extend(
                df.loc[label_indices, 'comment_text'].apply(len))

        clean_indices = df[df[ORDER_LABELS].sum(axis=1) == 0].index
        clean_lengths.extend(df.loc[clean_indices, 'comment_text'].apply(len))

        average_label_lengths = {label: np.mean(
            lengths) for label, lengths in label_lengths.items()}
        average_clean_length = np.mean(clean_lengths)

        data = {
            "Label": list(average_label_lengths.keys()) + ["Clean"],
            "Average Length (Characters)": list(average_label_lengths.values()) + [average_clean_length]
        }

        df_avg_lengths = pd.DataFrame(data)
        plt.figure(figsize=(10, 5))
        ax = sns.barplot(x="Average Length (Characters)",
                         y="Label", data=df_avg_lengths, palette='viridis')

        for i, v in enumerate(df_avg_lengths["Average Length (Characters)"]):
            ax.text(v + 0.5, i, str(round(v, 2)),
                    color='black', ha='left', va='center')

        plt.xlabel('Average Comment Length (Characters)')
        plt.ylabel('Label')
        plt.title('Average Comment Length for Each Label')

    # Graph 5
    elif graph_name == 'dstr_length':
        all_comment_lengths = df['comment_text'].apply(len).values

        plt.figure(figsize=(10, 5))
        ax = sns.boxplot(x=all_comment_lengths,
                         showfliers=False, palette='viridis')

        plt.xlabel('Number of Characters')
        plt.title('Distribution of Comment Lengths')

    # Graph 6 - Token Length per Label
    elif graph_name == 'token_length_per_label':
        label_token_lengths = {label: [] for label in ORDER_LABELS}
        clean_token_lengths = []

        for i, label in enumerate(ORDER_LABELS):
            label_indices = df[df[label] == 1].index
            label_token_lengths[label].extend(df.loc[label_indices, 'comment_text'].apply(
                lambda x: tokenize_text(x, tokenizer)))

        clean_indices = df[df[ORDER_LABELS].sum(axis=1) == 0].index
        clean_token_lengths.extend(df.loc[clean_indices, 'comment_text'].apply(
            lambda x: tokenize_text(x, tokenizer)))

        average_label_token_lengths = {label: np.mean(
            lengths) for label, lengths in label_token_lengths.items()}
        average_clean_token_length = np.mean(clean_token_lengths)

        data = {
            "Label": list(average_label_token_lengths.keys()) + ["Clean"],
            "Average Token Length": list(average_label_token_lengths.values()) + [average_clean_token_length]
        }

        df_avg_token_lengths = pd.DataFrame(data)
        plt.figure(figsize=(10, 5))
        ax = sns.barplot(x="Average Token Length", y="Label",
                         data=df_avg_token_lengths, palette='viridis')

        for i, v in enumerate(df_avg_token_lengths["Average Token Length"]):
            ax.text(v + 0.5, i, str(round(v, 2)),
                    color='black', ha='left', va='center')

        plt.xlabel('Average Token Length')
        plt.ylabel('Label')
        plt.title('Average Token Length for Each Label')

    # Graph 7 - Token Length
    elif graph_name == 'token_length_distribution':
        all_token_lengths = df['comment_text'].apply(
            lambda x: tokenize_text(x, tokenizer))

        plt.figure(figsize=(10, 5))
        ax = sns.boxplot(x=all_token_lengths,
                         showfliers=False, palette='viridis')

        plt.xlabel('Token Length')
        plt.ylabel('Frequency')
        plt.title('Distribution of Token Length for the Entire Dataset')
    else:
        print("Invalid graph name")

    if output_folder is not None:
        os.makedirs(output_folder, exist_ok=True)
        plt.savefig(os.path.join(output_folder, f'graph_{graph_name}.png'))
    else:
        plt.show()


def main():
    """
    Main function to load the data for toxic comment classification, set up a BERT model and run a training 

    - loads the dataset of specified length, batch size and transformations into a dataloader
    - sets up a BERT model for specified vocabulary size, model dimension, pretrained BERT base model, number of encoders and number of attention heads per encoder
    - starts training the BERT model

    """
    # Training (for cluster)

    # load the entire training data (length dataset_length) into train
    train_loader, test_loader = load_data("jigsaw_toxicity_pred", transformation=TOKENIZER,
                                          n_train=TRAIN_LENGTH, n_test=TEST_LENGTH, batch_size=BATCH_SIZE, shuffle=True)

    # visualization of plots
    # show(TOXIC +'train.csv', graph_name="dstr_toxic")  # plots without saving
    show((TOXIC +'train.csv'), output_folder=OUTPUT, graph_name="dstr_toxic")  # plots and saves in 'output_folder'
    # Note, that plotting number of tokens per label/distribution takes time to process, since data from csv is tokenized first

    # set up BERT model with toxic multi-label classification head
    berti = models.Model()

    # train model (device to be updated according to cluster GPU)
    training.TrainBERT(berti, train_loader, test_loader)


if __name__ == "__main__":
    main()

