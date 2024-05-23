from matplotlib import pyplot as plt
import os
import sys
from glob import glob
import soundfile as sf
import librosa
import pandas as pd
import numpy as np

home_dir = '../data/umich_swamp_aru_analysis/'
audio_dir = os.path.join(home_dir, 'audio_wav_22050')

def propose_events_of_interest(probs, start_times, end_times, fn, ebird_code, n_to_propose = 5, spacing = 5, threshold = 0.05):
    # probs (T,)
    # start_times (T,)
    # end_times (T,)
    # n_to_propose: number of events to propose
    # spacing: require event starts to be at least 3 seconds apart
    # threshold: omit predictions below threshold
    
    # boxcar filter
    probs_smoothed = (probs[1:] + probs[:-1])/2
    probs_smoothed = np.concatenate((probs[:1], probs_smoothed))
    
    # get most probable events
    prob_args = np.argsort(probs_smoothed)[::-1]
    
    intervals = []
    starts_used = []
    
    filename = []
    species_codes = []
    start_secs = []
    end_secs = []
    probabilities = []
    
    for i in range(len(prob_args)):
        j = prob_args[i]
        if (len(start_secs) == 0):
            ok_to_continue = True
        elif np.amin(np.abs([x-start_times[j] for x in start_secs]))>spacing:
            ok_to_continue = True
        else:
            ok_to_continue = False
        if ok_to_continue:
            prob = probs_smoothed[j]
            if prob<threshold:
                break
            start_time = start_times[j]
            end_time = min(np.amax(end_times), start_times[j]+4)
            
            filename.append(fn)
            species_codes.append(ebird_code)
            start_secs.append(start_time)
            end_secs.append(end_time)
            probabilities.append(prob)
            
        if len(start_secs)>=n_to_propose:
            break
            
    return pd.DataFrame({'filename' : filename, 
                         'Annotation' : species_codes, 
                         'Begin Time (s)' : start_secs, 
                         'End Time (s)' : end_secs, 
                         'Probability' : probabilities})



# Load files
output_dir = os.path.join(home_dir, 'outputs')
output_audio_dir = os.path.join(output_dir, 'audio')
output_spec_dir = os.path.join(output_dir, 'spectrograms')

for d in [output_dir, output_audio_dir, output_spec_dir]:
    if not os.path.exists(d):
        os.makedirs(d)
    
preds_dir = os.path.join(home_dir, 'msid', 'predictions')
preds_fps = sorted(glob(os.path.join(preds_dir, '*.npz')))
idx_to_ebird_fp = os.path.join(home_dir, 'msid', 'model_text_labels.txt')
idx_to_ebird = list(pd.read_csv(idx_to_ebird_fp,header=None)[0])

all_events = []

# find events of interest
for preds_fp in preds_fps:
    preds_np = np.load(preds_fp)
    
    probs = preds_np['probs']
    
    clip_starts = preds_np['clip_start_offsets']
    clip_ends = preds_np['clip_end_offsets']
    
    
    
    for sp in range(np.shape(probs)[1]):
        events = propose_events_of_interest(probs[:,sp], 
                                            clip_starts, 
                                            clip_ends, 
                                            os.path.basename(preds_fp), 
                                            idx_to_ebird[sp],
                                            threshold = 0.05)
        if len(events):
            all_events.append(events)
            
all_events = pd.concat(all_events).reset_index()
event_audio_fns = []
event_spec_fns = []

# get audio and spectrogram
for i, row in all_events.iterrows():
    fn = f"{i}_{row['Annotation']}"
    audio,sr = librosa.load(os.path.join(audio_dir, row['filename'].replace('.npz', '.wav')), offset=row['Begin Time (s)'], duration=4, sr=None)
    spec = np.abs(librosa.stft(audio))
    fig, ax = plt.subplots()
    img = librosa.display.specshow(librosa.amplitude_to_db(spec,ref=np.max),y_axis='log', x_axis='time', ax=ax)

    
    spec_fp = os.path.join(output_spec_dir, fn+'.png')
    audio_fp = os.path.join(output_audio_dir, fn+'.wav')
    
    plt.savefig(spec_fp)
    plt.close()
    
    sf.write(audio_fp, audio,sr)
    
    event_audio_fns.append(os.path.basename(audio_fp))
    event_spec_fns.append(os.path.basename(spec_fp))

all_events['Event Audio Filename'] = pd.Series(event_audio_fns)
all_events['Event Spec Filename'] = pd.Series(event_spec_fns)


all_events.to_csv(os.path.join(output_dir, 'events_of_interest.csv'))
    