import os, torch, pickle, torch, config, argparse, stats
from torch.utils.data import DataLoader, Dataset
from LangIdentDataset import RTDataset
from tqdm import tqdm
from GRUNetwork import RNN_GRU

def get_args():
    parser = argparse.ArgumentParser(
        description="")
    parser.add_argument("-M", "--trained_model", dest='model_name', type=str,
                        help="select trained model")
    args = parser.parse_args()
    return args

def langencoder(language_codes):
    one_hot_lang = {}
    lang2int = {lang : (num) for num, lang in dict(enumerate(language_codes)).items()}

    return lang2int

def load_model(path, config):
    model = path
    if config['device'] == 'gpu':
        device = torch.device('cuda:01')
    else:
        device = torch.device('cpu')
    with open(path, 'rb') as input_model:
        data = torch.load(input_model)
    trained_model = RNN_GRU(vocab_size=config['vocab_size'], seq_len=100, input_size=100,
               hidden_size=256, num_layers=2, output_size=10, device=device, dropout=0.0)
    trained_model.load_state_dict(data)
    return trained_model

def get_vocab(path):
    with open(path+'vocab.pkl', 'rb')as file:
        vocab = pickle.load(file)
    return vocab

def get_test_loader(path):

    with open(path, 'rb') as file:
        testing_loader = pickle.load(file)

    return testing_loader

def test_model(trained_model, test_data, language_stats, device, language_names_dict, int2lang):
    correct_per_example = 0
    total_predictions = 5000
    incorrect_guesses_per_instance = 0
    percent = 0
    example = 0
    batch_nr = 1
    tenp = 500
    num_characters = []
    count = 0
    for x, y in tqdm(test_data):
        batch_nr +=1
        example +=1
        hidden_layer = trained_model.init_hidden(1).to(device)
        for examples in zip(x,y):
            #total_predictions += 1
            count += 1
            prediction = trained_model(examples[0].unsqueeze(0).to(device), hidden_layer)
            _, indeces = torch.max(prediction[0].data, dim=1)
            characters = len(torch.nonzero(examples[0]))


            if indeces[0].item() == examples[1].item():
                num_characters.append(characters)
                correct_per_example += 1
                stats.update_stats(language_stats, indeces[0].item(), examples[1].item(), int2lang, characters, language_names_dict)
                break
            else:
                #characters = 0
                stats.update_stats(language_stats, indeces[0].item(), examples[1].item(), int2lang, characters, language_names_dict)
                incorrect_guesses_per_instance += 1
                continue

    print(example)
    print(correct_per_example)
    print(incorrect_guesses_per_instance)
    print(count)

    return language_stats

def main():
    print('Testing Model')
    CONFIG = config.get_config('config/config.json')
    if CONFIG['device'] == 'cpu':
        device = torch.device('cpu')
    else:
        device = 'cuda:01'
    language_codes = [i[1] for i in CONFIG['languages']]
    language_names = CONFIG['languages']
    lang2int = langencoder(language_codes)
    int2lang = {num : lang for lang, num in lang2int.items()}
    vocab = get_vocab('vocab/{}_'.format(args.model_name))
    trained_model = load_model('trained_models/{}.pt'.format(args.model_name), CONFIG).to(device)
    test_data = get_test_loader('dataloaders/{}_test_dataset.pkl'.format(args.model_name))
    language_names_dict = {i[1] : i[0] for i in language_names}
    language_stats = stats.gen_empty_stats(int2lang, language_names_dict)
    language_stats = test_model(trained_model, test_data, language_stats, device, language_names_dict, int2lang)
    evaluation = stats.further_analysis(language_stats, language_names,int2lang, language_names_dict)

if __name__ == '__main__':
    args = get_args()
    main()
