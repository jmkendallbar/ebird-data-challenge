from matplotlib import pyplot as plt
import os
import sys
import soundfile as sf
import pandas as pd
import numpy as np
from functools import partial
from glob import glob
import skimage.measure
from scipy.signal import convolve2d
from tqdm import tqdm

swamp_root_dir = "/home/jupyter/umich_swamp_aru_anaylsis/"

# Detection parameters based on some sweeps (recall .655 precision .956 at file level)
k_to_look_at = 3
threshold = 0.76
smoothing = 3
pooling = 1

# Taxonomy
ebird_taxonomy_fp = os.path.join(swamp_root_dir, "eBird_Taxonomy_v2022.csv")

# eBird / ML
swamp_checklists_fp = os.path.join(swamp_root_dir, "swamp_checklists.csv")
swamp_checklist_audio_assets_fp = os.path.join(swamp_root_dir, "swamp_checklist_audio_assets.csv")
swamp_hotspot_info_fp = os.path.join(swamp_root_dir, "ssw_hotspot_info.csv")

# ARU
swamp_aru_audio_assets_fp = os.path.join(swamp_root_dir, "swamp_aru_audio_assets.csv")
swamp_aru_audio_annotations_fp = os.path.join(swamp_root_dir, "swamp_aru_audio_annotations.csv")
swamp_aru_recorder_info_fp = os.path.join(swamp_root_dir, "swamp_aru_recorder_info.csv")

# Model Predictions
model_text_labels_fp = os.path.join(swamp_root_dir, "msid/model_text_labels.txt")
model_predictions_dir = os.path.join(swamp_root_dir, "msid/predictions/")
model_annotations_dir = os.path.join(swamp_root_dir, "msid/sliding_window_annotations/")

# eBird Frequency API
swamp_ebird_frequency_api_dir = os.path.join(swamp_root_dir, "msid/ebird_freq_api_responses/")

# Raw audio
swamp_audio_dir = os.path.join(swamp_root_dir, "swamp_audio_wav_22050")

# Weather
swamp_daily_weather_fp = os.path.join(swamp_root_dir, "swamp_daily_weather.csv")
swamp_hourly_weather_fp = os.path.join(swamp_root_dir, "swamp_hourly_weather.csv")

# Load assets df
swamp_aru_audio_assets_df = pd.read_csv(swamp_aru_audio_assets_fp)
swamp_aru_audio_assets_df['datetime'] = pd.to_datetime(swamp_aru_audio_assets_df['datetime'])

# Output fp
output_fn = "overall_predictions_with_uncertainty.csv"
output_fp = os.path.join(swamp_root_dir, output_fn)

# Load in the eBird Taxonomy

# eBird Taxonomy
ebird_taxonomy_df = pd.read_csv(ebird_taxonomy_fp)

species_taxonomy_df = []

for i, row in ebird_taxonomy_df.iterrows():
    if row['CATEGORY'] == 'species': 
        species_taxonomy_df.append({
            'species_code' : row['SPECIES_CODE'],
            'common_name' : row['PRIMARY_COM_NAME'],
            'sci_name' : row['SCI_NAME'],
            'taxon_order' : row['TAXON_ORDER'],
            'family' : row['FAMILY']
        })

species_taxonomy_df = pd.DataFrame(species_taxonomy_df)

# Load in the human drawn boxes
swamp_aru_audio_annotations_df = pd.read_csv(swamp_aru_audio_annotations_fp)

# create ebird mask
def create_ebird_freq_prediction_mask(model_text_labels, ebird_response_df, frequency_threshold=0, root_bird_label=0):
    
    species_filter = np.zeros_like(model_text_labels, dtype=np.float32)
    valid_species = ebird_response_df[ebird_response_df['frequency'] >= frequency_threshold]['species_code']
    
    valid_species = set(model_text_labels).intersection(valid_species)
    species_code_to_label = {species_code : label for label, species_code in enumerate(model_text_labels)}
    for species_code in valid_species:
        species_filter[species_code_to_label[species_code]] = 1.0
    
    if root_bird_label is not None:
        species_filter[root_bird_label] = 1
    
    return species_filter

annot_files = sorted(glob('/home/jupyter/umich_swamp_aru_anaylsis/msid/sliding_window_annotations/*.npz'))
to_txt = list(pd.read_csv('/home/jupyter/umich_swamp_aru_anaylsis/msid/model_text_labels.txt', header=None)[0])

def simple(probs, threshold = 0.5):
    x = np.amax(probs, axis = 0)>=threshold
    return x

def top_k(probs, threshold = 0.5, k=5, pooling = 1, smoothing = 1,mask=None):
    smoothing_kernel = np.full((smoothing,1), 1/smoothing)
    if smoothing>1:
        probs = convolve2d(probs,smoothing_kernel,mode='valid')
    if pooling>1:
        probs = skimage.measure.block_reduce(probs, (pooling,1), np.max)
    s = np.sort(probs, axis = 0)[::-1,:]
    soft_values = np.mean(s[:k,:],axis = 0) 
    
    if mask is not None:
        soft_values = soft_values * mask
    
    predictions = soft_values >= threshold
    return predictions, soft_values

def compare_results(gts, preds):

    gts = set(gts)
    preds = set(preds)
    
    intersection = set(gts).intersection(preds)
    
    if len(preds) > 0:
        precision = len(intersection) / len(preds) 
    else:
        precision = 1
    if len(gts) > 0: 
        recall = len(intersection) / len(gts)
    else:
        recall = 1
        
    if precision or recall:
        f1 = 2*precision*recall/(precision+recall)
    else:
        f1=0

    fns = gts.difference(preds)
    fps = preds.difference(gts)

    return {"Precision" : precision, "Recall" : recall, "F1":f1}

def evaluate(probs, labels, method):
    preds = method(probs)
    
    #
    predictions = []
    for i, p in enumerate(preds):
        if i == 0:
            continue
        if p:
            predictions.append(to_txt[i])
    return compare_results(labels, predictions)

all_predictions = []
all_scores = []

for i, asset_info in swamp_aru_audio_assets_df[swamp_aru_audio_assets_df["annotated"]==True].iterrows():
    asset_id = asset_info["asset_id"]

    x = np.load(os.path.join(model_predictions_dir, asset_id+".npz"))

    # eBird Frequency Response

    dt = asset_info['datetime']
    fn = f"{dt.year}-{dt.month}-{dt.day}.csv"
    ebird_frequency_response_fp = os.path.join(swamp_ebird_frequency_api_dir, fn)
    assert os.path.exists(ebird_frequency_response_fp)

    ebird_freq_response_df = pd.read_csv(ebird_frequency_response_fp)
    prediction_mask = create_ebird_freq_prediction_mask(to_txt, ebird_freq_response_df, frequency_threshold=0.01)
    
    predictions, scores = top_k(x['probs'], mask=prediction_mask, threshold=threshold, k=k_to_look_at, smoothing=smoothing)

    all_predictions.append(predictions)
    all_scores.append(scores)
    
all_predictions = np.stack(all_predictions, axis = 0)
all_scores = np.stack(all_scores, axis = 0)

results = {"species_code" : [], "overall_present" : [], "score" : []}
    
# assemble predictions
for i, species_code in enumerate(to_txt):
    if i == 0:
        continue
    
    preds_for_i = all_predictions[:,i]
    scores_for_i = all_scores[:,i]
    
    any_present = np.amax(preds_for_i)
    score = np.amax(scores_for_i)
        
    results['species_code'].append(species_code)
    results['overall_present'].append(any_present)
    results['score'].append(score)
    
results = pd.DataFrame(results)
results.to_csv(output_fp, index=False)