import config
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

from flask import Blueprint, render_template, request, jsonify

import config
from services import services_suggestion
# from data_services import database
# from services.services_middleware import session_required

query_bp = Blueprint('query', __name__)


vectorizers = {
    'game': None,
    'cpu': None,
    'ram': None,
    'gpu': None,
}

tfidf_matrices = {
    'game': None,
    'cpu': None,
    'ram': None,
    'gpu': None,
}


# Helper Functions
def compute_tfidf_matrix(names):
    vectorizer = TfidfVectorizer().fit(names)
    tfidf_matrix = vectorizer.transform(names)
    return vectorizer, tfidf_matrix

def get_games_list():
    names = config.game_data['name'][config.game_data['name'].isna().apply(lambda x: not x)]
    if vectorizers['game'] is None:
        vectorizers['game'], tfidf_matrices['game'] = compute_tfidf_matrix(names)
    return names[pd.isna(names).apply(lambda x : not x)]

def get_cpu_list():
    names = config.cpu_data['product'][config.cpu_data['product'].isna().apply(lambda x: not x)]
    if vectorizers['cpu'] is None:
        vectorizers['cpu'], tfidf_matrices['cpu'] = compute_tfidf_matrix(names)
    return names[pd.isna(names).apply(lambda x : not x)]

def get_ram_list():
    names = config.ram_data['Memory'][config.ram_data['Memory'].isna().apply(lambda x: not x)]
    if vectorizers['ram'] is None:
        vectorizers['ram'], tfidf_matrices['ram'] = compute_tfidf_matrix(names)
    return names[pd.isna(names).apply(lambda x : not x)]

def get_gpu_list():
    names = config.gpu_data['name'][config.gpu_data['name'].isna().apply(lambda x: not x)]
    if vectorizers['gpu'] is None:
        vectorizers['gpu'], tfidf_matrices['gpu'] = compute_tfidf_matrix(names)
    return names[pd.isna(names).apply(lambda x : not x)]

def order_completions(category, query, names, reverse=True):
    query_vec = vectorizers[category].transform([query])
    similarities = cosine_similarity(query_vec, tfidf_matrices[category]).flatten()
    completions = sorted(
        zip(names, similarities),
        key=lambda item: (item[0].lower() == query, item[1]),
        reverse=reverse
    )
    return [name for name, _ in completions]


def get_game_row(game, std_=False, dict_=True):
    game_row = config.game_data[config.game_data['name'] == game]
    if len(game_row) != 0:
        if std_:
            return config.std_game_data.loc[list(game_row.index)[0]]
        if dict_:
            return game_row.iloc[0].to_dict()
        return game_row.iloc[0]
    return None

def get_cpu_row(cpu, std_=False, dict_=True):
    cpu_row = config.cpu_data[config.cpu_data['product'] == cpu]
    if len(cpu_row) != 0:
        if std_:
            return config.std_cpu_data.loc[list(cpu_row.index)[0]]
        if dict_:
            return cpu_row.iloc[0].to_dict()
        return cpu_row.iloc[0]
    return None
    
def get_ram_row(ram, std_=False, dict_=True):
    ram_row = config.ram_data[config.ram_data['Memory'] == ram]
    if len(ram_row) != 0:
        if std_:
            return config.std_ram_data.loc[list(ram_row.index)[0]]
        if dict_:
            return ram_row.iloc[0].to_dict()
        return ram_row.iloc[0]
    return None
    
def get_gpu_row(gpu, std_=False, dict_=True):
    gpu_row = config.gpu_data[config.gpu_data['name'] == gpu]
    if len(gpu_row) != 0:
        if std_:
            return config.std_gpu_data.loc[list(gpu_row.index)[0]]
        if dict_:
            return gpu_row.iloc[0].to_dict()
        return gpu_row.iloc[0]
    return None


# Route Functions
@query_bp.route('/', methods=['GET'])
def home():
    return render_template('index.html')


@query_bp.route('/game', methods=['GET'])
def fetch_games():
    query = request.args.get('name', '').strip().lower()
    auto_completions = order_completions('game', query, get_games_list())
    return jsonify(auto_completions[:10])


@query_bp.route('/component')
def fetch_components():
    query = request.args.get('name', '').strip()
    category = request.args.get('category', '').strip().lower()

    if category == 'cpu':
        auto_completions = order_completions(category, query, get_cpu_list())
    elif category == 'ram':
        auto_completions = order_completions(category, query, get_ram_list())
    elif category == 'gpu':
        auto_completions = order_completions(category, query, get_gpu_list())
    
    return jsonify(auto_completions[:10])


@query_bp.route('/specs', methods=['GET'])
def fetch_specs():
    game = request.args.get('game', '').strip()
    game_row = get_game_row(game)
    if game_row is not None:
        return jsonify(services_suggestion.get_pc_suggestions(game_row))
    return jsonify({'error' : 'No such game found'})


@query_bp.route("/check-compatibility", methods=["POST"])
def check_compatibility():
    data = request.json
    cpu = data.get('cpu', '').strip()
    ram = data.get('ram', '').strip()
    gpu = data.get('gpu', '').strip()

    if cpu == '' or ram == '' or gpu == '':
        return jsonify({
            'error' : 'CPU, RAM and GPU need to be mentioned'
        })

    cpu_row = get_cpu_row(cpu, std_=True, dict_=False)
    ram_row = get_ram_row(ram, std_=True, dict_=False)
    gpu_row = get_gpu_row(gpu, std_=True, dict_=False)

    if (cpu_row is not None) and (ram_row is not None) and (gpu_row is not None):
        score = services_suggestion.evaluate_triplet(cpu_row, ram_row, gpu_row)

        return jsonify({
            'score' : score,
            'decision' : 'Compatible' if not pd.isna(score) else 'Not Compatible'
        })
    
    return jsonify({
        'error' : 'An error occured! Please Try Again later..'
    })
