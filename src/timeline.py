from glob import glob
import os
import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

inputDir = '../data/umich_swamp_aru_analysis/'
filePath = os.path.join(inputDir, "swamp_aru_audio_assets.csv")
print("Expected file path:", filePath)
print("Does the file exist?", os.path.exists(filePath))

assets = pd.read_csv(filePath)

datetimestrs = []
for row_idx, row in assets.iterrows():
    datetimestrs.append(f"{row['year']} {row['month']} {row['day']} {row['hour']:02d}:{row['minute']:02d}:{row['second']:02d}")

df = {"start": [], "end": [], "site":[]}
for row_idx, row in assets.iterrows():
    d = datetime.datetime.strptime(datetimestrs[row_idx], "%Y %m %d %H:%M:%S")
    dd = datetime.timedelta(0,row['duration'])
    df["site"].append(int(row["site_num"][1:]))
    df["start"].append(d)
    df["end"].append(d+dd)
    
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
            )
        ) for row_idx, row in df.iterrows()
    ] 
)

fig.update_layout(legend=dict(yanchor="bottom",y=0.01),margin=dict(l=0, r=0, b=0, t=0), autosize=False, width=600, height=200)
fig.write_html(
    os.path.join(inputDir, "timeline.html"),
    div_id='plotly_div'#,
   #post_script=create_javascript()
)
