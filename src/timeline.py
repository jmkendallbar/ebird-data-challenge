import os
import sys
import json
import datetime
import numpy as np
import pandas as pd

import plotly.graph_objects as go

def create_javascript(code_names, common_names, data_examples, n_examples_per_species=5):

    code_names = [ '"' + cn + '"' for cn in code_names ]
    common_names = [ '"' + cn + '"' for cn in common_names ]

    js = f"""

        let code_names = [{','.join(code_names)}]
        let common_names = [{','.join(common_names)}]
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

        let speciesDropdownDiv = document.createElement('div');
        speciesDropdownDiv.setAttribute("id", "species_dropdown_div")
        let speciesDropdown = document.createElement('select')
        speciesDropdown.setAttribute("id", "species_dropdown_select")

        //Create and append the options for dropdown
        for (let i = 0; i < code_names.length + 1; i++) {{
            let option = document.createElement("option");
            if (i == 0){{
                option.value = "all";
                option.text = "all";
            }}else{{
                option.value = code_names[i-1];
                option.text = common_names[i-1];
            }}
            speciesDropdown.appendChild(option);
        }}

        //Add action for dropdown
        speciesDropdown.onchange = function(){{
            let species_code_name = document.getElementById('species_dropdown_select').value
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
                if (fig.data[i].meta.includes(species_code_name) && species_code_name != 'all'){{ 
                    // If relevant to selected species
                    fig.data[i].line.color="red"
                }} else {{
                    // If not relevant to selected species
                    fig.data[i].line.color="black"
                }}
            }}
            Plotly.newPlot('plotly_div', fig.data, fig.layout)
        }}
        speciesDropdownDiv.appendChild(speciesDropdown)
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


def main(workshop_fp):
    assets = pd.read_csv(os.path.join(workshop_fp, "swamp_aru_audio_assets.csv"))
    birdnet_names = pd.read_csv(os.path.join(workshop_fp, "birdnet/model_text_labels.txt"),header=None)
    taxonomy = pd.read_csv(os.path.join(workshop_fp, "eBird_Taxonomy_v2022.csv"))
    events_of_interest = pd.read_csv(os.path.join(workshop_fp, "outputs", "events_of_interest.csv"))

    code_names = []; common_names = []
    for _, birdnet_name in  birdnet_names.iloc[1:].iterrows():
        code_name = birdnet_name[0]
        code_names.append(code_name)
        common_names.append(taxonomy[taxonomy["SPECIES_CODE"] == code_name]["PRIMARY_COM_NAME"].item())

    events_of_interest['basename'] = events_of_interest['filename'].map(lambda fn: fn.split(".")[0])

    datetimestrs = []
    for row_idx, row in assets.iterrows():
        datetimestrs.append(f"{row['year']} {row['month']} {row['day']} {row['hour']:02d}:{row['minute']:02d}:{row['second']:02d}")

    df = {"start": [], "end": [], "site":[], "code_names":[]}
    for row_idx, row in assets.iterrows():
        d = datetime.datetime.strptime(datetimestrs[row_idx], "%Y %m %d %H:%M:%S")
        dd = datetime.timedelta(0,row['duration'])
        df["site"].append(int(row["site_num"][1:]))
        df["start"].append(d)
        df["end"].append(d+dd)
        df["code_names"].append("|".join([event['Annotation'] for event_idx, event in events_of_interest[row["asset_id"] == events_of_interest['basename']].iterrows()]))

    df = pd.DataFrame(df)

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
        ] 
    )

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

    fig.update_layout(showlegend=False,margin=dict(l=0, r=0, b=0, t=0), autosize=False, width=600, height=200)
    fig.write_html(
        os.path.join(workshop_fp, "timeline.html"),
        div_id='plotly_div',
    post_script=create_javascript(code_names, common_names, data_examples)
    )


if __name__ == "__main__":
    input_dir = sys.argv[1]
    print("Expected file path:", input_dir)
    print("Does the file exist?", os.path.exists(input_dir))
    main(input_dir)
