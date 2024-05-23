import os
import sys
import json
import datetime
import numpy as np
import pandas as pd

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px


def create_javascript(code_names, common_names, present_absent, scores, data_examples, n_examples_per_species=5):

    score_idxs = np.argsort(scores)
    code_names = [code_names[i] for i in score_idxs]
    common_names = [common_names[i] for i in score_idxs]

    absent_code_names = [cn for i, cn in enumerate(code_names) if not present_absent[i]]
    absent_common_names = [cn + f" ({scores[score_idxs[i]]:.03f})" for i, cn in enumerate(common_names) if not present_absent[i]]
    present_code_names = [cn for i, cn in enumerate(code_names) if present_absent[i]]
    present_common_names = [cn + f" ({scores[score_idxs[i]]:.03f})" for i, cn in enumerate(common_names) if present_absent[i]]

    absent_code_names = [ '"' + cn + '"' for cn in code_names ]
    absent_common_names = [ '"' + cn + '"' for cn in absent_common_names ]
    present_code_names = [ '"' + cn + '"' for cn in present_code_names ]
    present_common_names = [ '"' + cn + '"' for cn in present_common_names ]

    js = f"""

        let absent_code_names = [{','.join(absent_code_names)}]
        let absent_common_names = [{','.join(absent_common_names)}]
        let present_code_names = [{','.join(present_code_names)}]
        let present_common_names = [{','.join(present_common_names)}]
        let n_examples = {n_examples_per_species}
        let data_examples = {json.dumps(data_examples)}
        let highlight_colors = ["#961703", "#b81c04", "#d11e02", "#e82102", "#f72605"]

        //Add media viewing functions
        function playSound(fp){{
            var sound = new Audio(fp)
            sound.play()
            sound.onended = function(){{
                this.currentSrc = null
                this.src = ''
                this.srcObject = null
                this.remove()
            }}
        }}
        function playSoundFromSpectrogram(i_str){{
            let imgElem = document.getElementById("spectrogram_" + i_str)
            let wav_src = imgElem.src.replace(".png", ".wav").replace('spectrograms','audio')
            playSound(wav_src)
        }}
        function highlightRecording(i, turn_on){{
            let species_code_name = document.getElementById('species_dropdown_select').value
            let fig = document.getElementById('plotly_div')
            let j = data_examples[species_code_name]['rec_id'][i]
            if (turn_on){{
                fig.data[j].line.color="pink"
            }} else {{
                //Go back to highlight but not hover color
                fig.data[j].line.color="red"
            }}
            Plotly.newPlot('plotly_div', fig.data, fig.layout)
        }}
        function updateSpecies(dropdown_name, unused_dropdown_name){{
            // Set the unused dropdown to null option
            document.getElementById(unused_dropdown_name).value = "null"
            // Set the species properly for the rest of the 
            let species_code_name = document.getElementById(dropdown_name).value
            let n_examples_this_species = data_examples[species_code_name]['fn'].length
            for (let i=0; i<n_examples;i++){{
                let i_str = i.toString()
                if (species_code_name == "all" || i >= n_examples_this_species){{
                    document.getElementById('media_viewer_' + i_str).style.visibility = 'hidden'
                }} else {{
                    document.getElementById('media_viewer_' + i_str).style.visibility = 'visible'
                    document.getElementById('spectrogram_' + i_str).src = "./spectrograms/" + data_examples[species_code_name]['fn'][i]
                    document.getElementById('spectrogram_' + i_str).style.visibility = 'visible'
                    document.getElementById('text_' + i_str).innerHTML = "Probability: " + data_examples[species_code_name]['p'][i].toString()
                }}
            }}
            let fig = document.getElementById('plotly_div')
            for (let i=0; i<fig.data.length; i++){{
                if (fig.data[i].meta === undefined){{
                    console.log("not messing with " + i.toString())
                }} else if (fig.data[i].name.includes('e-bird')) {{
                    if (fig.data[i].meta.includes(species_code_name)){{
                        // If relevant to selected species
                        fig.data[i].visible=true
                    }} else {{
                        // If not relevant to selected species
                        fig.data[i].visible=false
                    }}
                }} else {{
                    if (fig.data[i].meta.includes(species_code_name) && species_code_name != 'all'){{ 
                        // If relevant to selected species
                        fig.data[i].line.color="red"
                    }} else {{
                        // If not relevant to selected species
                        fig.data[i].line.color="black"
                    }}
                }}
            }}
            Plotly.newPlot('plotly_div', fig.data, fig.layout)
        }}

        let speciesDropdownDiv = document.createElement('div');
        speciesDropdownDiv.setAttribute("id", "species_dropdown_div")
        let presentSpeciesDropdown = document.createElement('select')
        presentSpeciesDropdown.setAttribute("id", "present_species_dropdown_select")
        let absentSpeciesDropdown = document.createElement('select')
        absentSpeciesDropdown.setAttribute("id", "absent_species_dropdown_select")

        //Create and append the options for dropdown
        for (let i = 0; i < present_code_names.length + 1; i++) {{
            let option = document.createElement("option");
            if (i == 0){{
                option.value = "null";
                option.text = "Choose present species";
                option.disabled=true
                option.selected=true
                option.hidden=true
            }}else{{
                option.value = present_code_names[i-1];
                option.text = present_common_names[i-1];
            }}
            presentSpeciesDropdown.appendChild(option);
        }}

        //Create and append the options for dropdown
        for (let i = 0; i < absent_code_names.length + 1; i++) {{
            let option = document.createElement("option");
            if (i == 0){{
                option.value = "null";
                option.text = "Choose absent species";
                option.disabled=true
                option.selected=true
                option.hidden = true
            }}else{{
                option.value = absent_code_names[i-1];
                option.text = absent_common_names[i-1];
            }}
            absentSpeciesDropdown.appendChild(option);
        }}

        //Add action for dropdown
        presentSpeciesDropdown.onchange = function() {{ updateSpecies('present_species_dropdown_select', 'absent_species_dropdown_select') }}
        absentSpeciesDropdown.onchange = function() {{ updateSpecies('absent_species_dropdown_select', 'present_species_dropdown_select') }}
        speciesDropdownDiv.appendChild(presentSpeciesDropdown)
        speciesDropdownDiv.appendChild(absentSpeciesDropdown)
        document.body.appendChild(speciesDropdownDiv);

        // Add media viewing space 
        for (let i=0; i < n_examples; i++){{
            let i_str = i.toString()
            let elemDiv = document.createElement('div');
            elemDiv.setAttribute("id", "media_viewer_" + i_str);
            let elemTxt = document.createElement('p')
            elemTxt.setAttribute("id", "text_" + i_str);
            elemTxt.innerHTML = ""
            elemDiv.appendChild(elemTxt)
            let elemImg = document.createElement('img')
            elemImg.setAttribute("id", "spectrogram_" + i_str)
            elemImg.setAttribute("style", "cursor:pointer;visibility:hidden")
            elemImg.setAttribute("src", "")
            elemImg.setAttribute("width", 200)
            // elemImg.setAttribute("onclick", "document.getElementById('audio_" + i_str + "').play()")
            elemImg.onclick = function() {{ playSoundFromSpectrogram(i_str); }};
            elemImg.onmouseover = function() {{ highlightRecording(i_str, true); }};
            elemImg.onmouseout = function() {{ highlightRecording(i_str, false); }};
            elemDiv.appendChild(elemImg)
            // let elemAudio = document.createElement("audio")
            // elemAudio.setAttribute("id", "audio_" + i_str)
            // elemAudio.setAttribute("src", "")
            // elemAudio.setAttribute("type", "audio/wav")
            // elemDiv.appendChild(elemAudio)
            document.body.appendChild(elemDiv);
        }}
    
    """

    return js

def get_names(birdnet_names, taxonomy):
    code_names = []; common_names = []
    for _, birdnet_name in  birdnet_names.iloc[1:].iterrows():
        code_name = birdnet_name[0]
        code_names.append(code_name)
        common_names.append(taxonomy[taxonomy["SPECIES_CODE"] == code_name]["PRIMARY_COM_NAME"].item())
    return code_names, common_names

def format_events_of_interest(code_names, assets, events_of_interest):
    data_examples = {}
    for code_name in code_names:
        data_examples[code_name] = {"fn":[], "p":[], "rec_id":[]}
        for row_idx, row in events_of_interest[events_of_interest['Annotation'] == code_name].iterrows():
            data_examples[code_name]['fn'].append(row['Event Spec Filename'])
            data_examples[code_name]['p'].append(row['Probability'])
            data_examples[code_name]['rec_id'].append(assets[row['basename'] == assets["asset_id"]].index.item())
        sort_idxs = np.argsort(data_examples[code_name]['p'])[::-1]
        data_examples[code_name]['fn'] = [data_examples[code_name]['fn'][i] for i in sort_idxs]
        data_examples[code_name]['p'] = [data_examples[code_name]['p'][i] for i in sort_idxs]
    return data_examples

def recorders_overview(assets, events_of_interest, ebird_checklists):

    datetimestrs = []
    for row_idx, row in assets.iterrows():
        datetimestrs.append(f"{row['year']}-{row['month']}-{row['day']} {row['hour']:02d}:{row['minute']:02d}:{row['second']:02d}")

    df = {"start": [], "end": [], "site":[], "code_names":[]}
    for row_idx, row in assets.iterrows():
        d = datetime.datetime.strptime(datetimestrs[row_idx], "%Y-%m-%d %H:%M:%S")
        dd = datetime.timedelta(0,row['duration'])
        df["site"].append(int(row["site_num"][1:]))
        df["start"].append(d)
        df["end"].append(d+dd)
        df["code_names"].append("|".join([event['Annotation'] for event_idx, event in events_of_interest[row["asset_id"] == events_of_interest['basename']].iterrows()]))

    df = pd.DataFrame(df)

    ## Get overall ebird intervals 
    S = []
    for row_idx, row  in ebird_checklists.iterrows():
        start = datetime.datetime.strptime(row['datetime'], "%Y-%m-%d %H:%M:%S")
        end =  datetime.datetime.strptime(row['end_time'].split(".")[0], "%Y-%m-%d %H:%M:%S")
        S.append((start, end))
    S = list(set(S))

    ebird_df = {"start": [], "end": [], "site":[]}
    for start_time, end_time in S:
        ebird_df["site"].append(-1)
        ebird_df["start"].append(start_time)
        ebird_df["end"].append(end_time)

    ebird_df = pd.DataFrame(ebird_df)

    ## Get specific ebird intervals
    specific_ebird_df = {"start": [], "end": [], "site":[], "code_name":[]}
    for row_idx, row in ebird_checklists.iterrows():
        start = datetime.datetime.strptime(row['datetime'], "%Y-%m-%d %H:%M:%S")
        end =  datetime.datetime.strptime(row['end_time'].split(".")[0], "%Y-%m-%d %H:%M:%S")
        specific_ebird_df["site"].append(int(row['closest_ARU_id']))
        specific_ebird_df["start"].append(start)
        specific_ebird_df["end"].append(end)
        specific_ebird_df["code_name"].append(row['species_codes'])

    specific_ebird_df = pd.DataFrame(specific_ebird_df)

    fig = go.Figure(data=
        [ 
            go.Scatter(
                x=[row['start'], row['end']],
                y=[row['site'], row['site']],
                mode='lines',
                line=dict(
                    color="black",
                    width=10
                ),
                name = f"{row['site']}",
                meta = row['code_names'].split("|")
            ) for row_idx, row in df.iterrows()
        ] + 
        [
            go.Scatter(
                x=[row['start'], row['end']],
                y=[row['site'], row['site']],
                mode='lines',
                line=dict(
                    color="blue",
                    width=10
                ),
                name = "all e-bird"
            ) for row_idx, row in ebird_df.iterrows()            
        ] + 
        [
            go.Scatter(
                x=[row['start'], row['end']],
                y=[row['site'], row['site']],
                mode='lines',
                line=dict(
                    color='rgba(0, 255, 0, 0.01)',
                    width=10
                ),
                visible=False,
                name=f"e-bird {row['code_name']}",
                meta = [row['code_name']]
            ) for row_idx, row in specific_ebird_df.iterrows()                
        ]
    )

    return fig

def hourly_species_distribution(events, taxonomy):

    # Filter out rows with Annotation 'bird1'
    events = events.copy()[events['Annotation'] != 'bird1']

    # Extract datetime from the filename
    def extract_datetime(filename):
        parts = filename.split('_')
        date_str = parts[4]
        time_str = parts[5][:6]
        datetime_str = f"{date_str}{time_str}"
        return datetime.datetime.strptime(datetime_str, '%Y%m%d%H%M%S')

    # Apply the extraction function to the filenames
    events['datetime'] = events['filename'].apply(extract_datetime)
    events['hour'] = events['datetime'].dt.floor('H')  # Floor to the nearest hour

    # Merge events with taxonomy to get the family names
    events = events.merge(taxonomy[['SPECIES_CODE', 'FAMILY']], left_on='Annotation', right_on='SPECIES_CODE', how='left')

    # Group by hour and Family (instead of Annotation), then count occurrences
    hourly_data = events.groupby(['hour', 'FAMILY']).size().reset_index(name='count')

    # Calculate the total count per hour
    total_counts_per_hour = hourly_data.groupby('hour')['count'].sum().reset_index(name='total_count')

    # Merge the total counts back with the original counts
    hourly_data = hourly_data.merge(total_counts_per_hour, on='hour')

    # Calculate the proportion of each family per hour
    hourly_data['percentage'] = hourly_data['count'] / hourly_data['total_count']

    # Create the proportional stacked area plot
    fig = px.area(hourly_data, x='hour', y='percentage', color='FAMILY', 
                labels={'percentage': 'Proportion', 'hour': 'Time (Hour)', 'FAMILY': 'Bird Family'},
                title='Proportion of Bird Families per Hour Over 3 Days')
    
    return fig


def main(workshop_fp):

    ## Load data
    assets = pd.read_csv(os.path.join(workshop_fp, "swamp_aru_audio_assets.csv"))
    birdnet_names = pd.read_csv(os.path.join(workshop_fp, "birdnet/model_text_labels.txt"),header=None)
    taxonomy = pd.read_csv(os.path.join(workshop_fp, "eBird_Taxonomy_v2022.csv"))
    events_of_interest = pd.read_csv(os.path.join(workshop_fp, "outputs", "events_of_interest.csv"))
    events_of_interest['basename'] = events_of_interest['filename'].map(lambda fn: fn.split(".")[0])
    ebird_checklists = pd.read_csv(os.path.join(workshop_fp, "ebird_checklists_species_breakdown_with_start_end_time.csv"))

    ## Get names for plotting
    code_names, common_names = get_names(birdnet_names, taxonomy)
    data_examples = format_events_of_interest(code_names, assets, events_of_interest)

    ## Format presence absent data
    present_absent = np.random.binomial(1, 0.5, size=len(code_names))
    scores = np.random.rand(len(code_names))


    # Combine the figures into subplots
    fig = make_subplots(rows=2, cols=1, subplot_titles=('Recorders', 'Bird Species Proportion'))

    # Add traces from fig1
    fig1 = recorders_overview(assets, events_of_interest, ebird_checklists)
    for trace in fig1.data:
        fig.add_trace(trace, row=1, col=1)

    # Add traces from fig2
    fig2 = hourly_species_distribution(events_of_interest, taxonomy)
    for trace in fig2.data:
        fig.add_trace(trace, row=2, col=1)

    fig.update_layout(showlegend=False,margin=dict(l=0, r=0, b=0, t=0), autosize=False, width=1200, height=400)
    fig.write_html(
        os.path.join(workshop_fp, "timeline.html"),
        div_id='plotly_div',
        post_script=create_javascript(code_names, common_names, present_absent, scores, data_examples)
    )

if __name__ == "__main__":
    input_dir = sys.argv[1]
    print("Expected file path:", input_dir)
    print("Does the file exist?", os.path.exists(input_dir))
    main(input_dir)
