import re
import pandas as pd
import numpy as np

import config


def parse_opengl_version(version):
    if pd.isnull(version):
        return -1
    
    version = str(version).strip().lower()
    
    if version.startswith('es'):
        match = re.match(r'es\s*(\d+)\.(\d+)', version)
        if match:
            major = int(match.group(1))
            minor = int(match.group(2))
            return major + minor / 10 - 1
        return 0

    version = re.sub(r'\s*\(.*?\)', '', version)

    parts = version.split('.')
    if len(parts) == 2:
        major, minor = int(parts[0]), int(parts[1])
        return major + minor / 10
    elif len(parts) == 3:
        major, minor, patch = map(int, parts)
        return major + minor / 10 + patch / 1000
    elif len(parts) == 1:
        return float(parts[0])
    
    return -1


def parse_directx_version(version):
    if pd.isnull(version):
        return -1
    
    version = str(version).strip().lower()

    if version == '12 ultimate':
        return 12.9

    match = re.match(r'(\d+)(?:\.(\d+))?([a-c])?', version)
    if not match:
        return -1
    
    major = int(match.group(1))
    minor = int(match.group(2)) if match.group(2) else 0
    suffix = match.group(3)

    suffix_val = {'a': 0.1, 'b': 0.2, 'c': 0.3}.get(suffix, 0)

    return major + minor / 10 + suffix_val


def is_cpu_compatible(cpu_row, game_row):
    if cpu_row['max_frequency'] < game_row['minimum_clock_speed'] or \
        cpu_row['base_frequency'] < game_row['minimum_clock_speed'] or \
        cpu_row['max_memory_size'] < game_row['minimum_memory']:
        return 0
    
    if cpu_row['base_frequency'] == game_row['recommended_clock_speed'] and \
        cpu_row['max_memory_size'] > game_row['recommended_memory']:
        return 1

    return 0.5


def is_ram_compatible(mem_row, game_row):
    if mem_row['Capacity'] < game_row['minimum_memory']:
        return 0
    if mem_row['Capacity'] == game_row['recommended_memory']:
        return 1
    return 0.5


def is_gpu_compatible(gpu_row, game_row):
    if gpu_row['memory_size'] < game_row['minimum_vram'] or \
        gpu_row['shader_model'] < float(game_row['minimum_shader_model']) or \
        parse_directx_version(gpu_row['directx']) < parse_directx_version(game_row['minimum_directx']) or \
        parse_opengl_version(gpu_row['opengl']) < parse_opengl_version(game_row['minimum_opengl']):
        return 0

    if gpu_row['memory_size'] == game_row['recommended_vram'] and \
        gpu_row['shader_model'] == float(game_row['recommended_shader_model']) and \
        parse_directx_version(gpu_row['directx']) == parse_directx_version(game_row['recommended_directx']) and \
        parse_opengl_version(gpu_row['opengl']) == parse_opengl_version(game_row['recommended_opengl']):
        return 1

    return 0.5


def get_top_k_ram(ram_data, game_row, k=10):
    candidates = ram_data.\
            apply(lambda row: is_ram_compatible(row.to_dict(), game_row), axis=1).\
            sort_values(ascending=False).head(k)
    indices = candidates[candidates != 0].index
    filtered = ram_data.loc[indices].copy(deep=True).reset_index()
    std_filtered = config.std_ram_data.loc[indices].copy(deep=True)
    return filtered, std_filtered


def get_top_k_gpu(gpu_data, game_row, k=10):
    candidates = gpu_data.\
            apply(lambda row: is_gpu_compatible(row.to_dict(), game_row), axis=1).\
            sort_values(ascending=False).head(k)
    indices = candidates[candidates != 0].index
    filtered = gpu_data.loc[indices].copy(deep=True).reset_index()
    std_filtered = config.std_gpu_data.loc[indices].copy(deep=True)
    return filtered, std_filtered


def get_top_k_cpu(cpu_data, game_row, k=10):
    candidates = cpu_data.\
            apply(lambda row: is_cpu_compatible(row.to_dict(), game_row), axis=1).\
            sort_values(ascending=False).head(k)
    indices = candidates[candidates != 0].index
    filtered = cpu_data.loc[indices].copy(deep=True).reset_index()
    std_filtered = config.std_cpu_data.loc[indices].copy(deep=True)
    return filtered, std_filtered


def form_triplets(cpus, rams, gpus, std=True):
    triplets = []
    if std:
        for _, cpu in cpus.iterrows():
            for _, ram in rams.iterrows():
                for _, gpu in gpus.iterrows():
                    triplets.append((cpu, ram, gpu))
    else:
        for _, cpu in cpus.iterrows():
            for _, ram in rams.iterrows():
                for _, gpu in gpus.iterrows():
                    triplets.append(((cpu['index'], cpu['product']), (ram['index'], ram['Memory']), (gpu['index'], gpu['name'])))
    return triplets


def evaluate_triplet(cpu, ram, gpu):
    normalized_vector = np.array(pd.concat([cpu, ram])).reshape(1, -1)
    cpu_ram_recon_error = np.mean(np.sqrt((config.cpu_ram_encoder.predict(normalized_vector) - normalized_vector) ** 2))
    if cpu_ram_recon_error > config.COMPATIBILITY_THRESHOLD[0]:
        return np.nan

    normalized_vector = np.array(pd.concat([cpu, gpu])).reshape(1, -1)
    cpu_gpu_recon_error = np.mean(np.sqrt((config.cpu_gpu_encoder.predict(normalized_vector) - normalized_vector) ** 2))
    if cpu_gpu_recon_error > config.COMPATIBILITY_THRESHOLD[1]:
        return np.nan
    
    return cpu_gpu_recon_error * cpu_ram_recon_error


def get_sentiment(cpu, ram, gpu):
    gcpu_sent = config.cpu_gpu_sentiment.loc[
        (config.cpu_gpu_sentiment['cpu'] == cpu) & (config.cpu_gpu_sentiment['gpu'] == gpu), 
        'sentiment']
    gcpu_sent = gcpu_sent.values[0] if not gcpu_sent else 0

    rcpu_sent = config.cpu_ram_sentiment.loc[
        (config.cpu_ram_sentiment['cpu'] == cpu) & (config.cpu_ram_sentiment['ram'] == ram), 
        'sentiment']
    rcpu_sent = rcpu_sent.values[0] if not rcpu_sent else 0
    
    return {'gcpu_sent' : gcpu_sent, 'rcpu_sent' : rcpu_sent}


def get_association(cpu, ram, gpu):
    values = {}

    indices = cpu['index'], ram['index']
    match_ = config.arm_cpu_ram[(config.arm_cpu_ram['CPU'] == indices[0]) & (config.arm_cpu_ram['Memory'] == indices[1])]
    for key, value in match_[['Support', 'Confidence', 'Lift']].to_dict().items():
        values[f'cpu_ram_{key.lower()}'] = value.get(0, np.nan)

    indices = cpu['index'], gpu['index']
    match_ = config.arm_cpu_gpu[(config.arm_cpu_gpu['CPU'] == indices[0]) & (config.arm_cpu_gpu['GPU'] == indices[1])]
    for key, value in match_[['Support', 'Confidence', 'Lift']].to_dict().items():
        values[f'cpu_gpu_{key.lower()}'] = value.get(0, np.nan)

    return values


def batch_evaluate_triplets(std_triplets):
    cpu_list, ram_list, gpu_list = zip(*std_triplets)

    cpu_df = pd.DataFrame(cpu_list).reset_index(drop=True)
    ram_df = pd.DataFrame(ram_list).reset_index(drop=True)
    gpu_df = pd.DataFrame(gpu_list).reset_index(drop=True)

    cpu_ram_combined = pd.concat([cpu_df, ram_df], axis=1)
    cpu_gpu_combined = pd.concat([cpu_df, gpu_df], axis=1)

    cpu_ram_pred = config.cpu_ram_encoder.predict(cpu_ram_combined)
    cpu_gpu_pred = config.cpu_gpu_encoder.predict(cpu_gpu_combined)

    cpu_ram_errors = np.mean(np.sqrt((cpu_ram_pred - cpu_ram_combined.values) ** 2), axis=1)
    cpu_gpu_errors = np.mean(np.sqrt((cpu_gpu_pred - cpu_gpu_combined.values) ** 2), axis=1)

    mask = (cpu_ram_errors <= config.COMPATIBILITY_THRESHOLD[0]) & (cpu_gpu_errors <= config.COMPATIBILITY_THRESHOLD[1])
    scores = np.where(mask, cpu_ram_errors * cpu_gpu_errors, np.nan)

    return scores


def batch_evaluate_triplets_one(std_triplets):
    cpu_list, ram_list, gpu_list = zip(*std_triplets)

    cpu_df = pd.DataFrame(cpu_list).reset_index(drop=True)
    ram_df = pd.DataFrame(ram_list).reset_index(drop=True)
    gpu_df = pd.DataFrame(gpu_list).reset_index(drop=True)

    cpu_ram_combined = pd.concat([cpu_df, ram_df], axis=1)
    cpu_gpu_combined = pd.concat([cpu_df, gpu_df], axis=1)

    cpu_ram_pred = config.cpu_ram_encoder.predict(cpu_ram_combined)
    cpu_gpu_pred = config.cpu_gpu_encoder.predict(cpu_gpu_combined)

    cpu_ram_errors = np.mean(np.sqrt((cpu_ram_pred - cpu_ram_combined.values) ** 2), axis=1)
    cpu_gpu_errors = np.mean(np.sqrt((cpu_gpu_pred - cpu_gpu_combined.values) ** 2), axis=1)

    sentiments = [
        get_sentiment(
            cpu=cpu_list[idx], 
            ram=ram_list[idx], 
            gpu=gpu_list[idx]
        ) for idx in range(len(std_triplets))
    ]

    associations = [
        get_association(
            cpu=cpu_list[idx], 
            ram=ram_list[idx], 
            gpu=gpu_list[idx]
        ) for idx in range(len(std_triplets))]

    mask = (cpu_ram_errors <= config.COMPATIBILITY_THRESHOLD[0]) & (cpu_gpu_errors <= config.COMPATIBILITY_THRESHOLD[1])
    scores = np.where(mask, cpu_ram_errors * cpu_gpu_errors, np.nan)

    return scores


def get_pc_suggestions(game_row):
    top_cpus, top_std_cpus = get_top_k_cpu(config.cpu_data, game_row)
    top_rams, top_std_rams = get_top_k_ram(config.ram_data, game_row)
    top_gpus, top_std_gpus = get_top_k_gpu(config.gpu_data, game_row)

    triplets = form_triplets(top_cpus, top_rams, top_gpus, std=False)
    if len(triplets) != 0:
        std_triplets = form_triplets(top_std_cpus, top_std_rams, top_std_gpus)
        scores = batch_evaluate_triplets(std_triplets)
        indices = np.where(pd.Series(pd.isna(scores)).apply(lambda x: not x))[0]
        triplets = [triplets[idx] for idx in indices]

    return triplets
