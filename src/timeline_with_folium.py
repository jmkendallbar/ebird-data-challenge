from glob import glob
import os
import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from folium.plugins import TimestampedGeoJson

# Define input directory and file paths
inputDir = '../data/umich_swamp_aru_analysis/'
outputDir = '../outputs/'
filePath = os.path.join(inputDir, "swamp_aru_audio_assets.csv")
recorder_info_path = os.path.join(inputDir, "swamp_aru_recorder_info.csv")
eventsfilePath = os.path.join(outputDir, "schmidt_events_of_interest.csv")
taxonomyFilePath = os.path.join(inputDir, "eBird_Taxonomy_v2022.csv")

# Read the assets CSV file
assets = pd.read_csv(filePath)

# Read the events CSV file
events = pd.read_csv(eventsfilePath)

# Read the taxonomy CSV file
taxonomy = pd.read_csv(taxonomyFilePath)

# Filter out rows with Annotation 'bird1'
events = events[events['Annotation'] != 'bird1']

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

fig.show()



# Prepare datetime strings
datetimestrs = []
for row_idx, row in assets.iterrows():
    datetimestrs.append(f"{row['year']} {row['month']} {row['day']} {row['hour']:02d}:{row['minute']:02d}:{row['second']:02d}")

# Create dataframe with start, end, and site information
df = {"start": [], "end": [], "site":[]}
for row_idx, row in assets.iterrows():
    d = datetime.datetime.strptime(datetimestrs[row_idx], "%Y %m %d %H:%M:%S")
    dd = datetime.timedelta(0,row['duration'])
    df["site"].append(int(row["site_num"][1:]))
    df["start"].append(d)
    df["end"].append(d+dd)
    
df = pd.DataFrame(df)

# Read the recorder info CSV
recorder_info = pd.read_csv(recorder_info_path)

# Merge the recorder info with the asset data
df = pd.merge(df, recorder_info, left_on='site', right_on='site_num')

# Prepare data for Folium
location_data = []
for _, row in df.iterrows():
    location_data.append({
        'site': row['site'],
        'start': row['start'],
        'end': row['end'],
        'lat': row['latitude'],
        'lon': row['longitude']
    })

# Create a Folium map with a time slider
m = folium.Map(location=[df['latitude'].mean(), df['longitude'].mean()], zoom_start=10)

features = []
for loc in location_data:
    feature = {
        'type': 'Feature',
        'geometry': {
            'type': 'Point',
            'coordinates': [loc['lon'], loc['lat']],
        },
        'properties': {
            'time': loc['start'].isoformat(),
            'popup': f"Site: {loc['site']}",
            'icon': 'circle',
            'iconstyle': {
                'color': 'red',
                'fillColor': 'red',
                'fillOpacity': 0.6,
                'radius': 5
            }
        }
    }
    features.append(feature)

TimestampedGeoJson(
    {'type': 'FeatureCollection', 'features': features},
    period='PT1M',  # Time period in ISO 8601 duration format
    add_last_point=True,
    auto_play=False,
    loop=False
).add_to(m)

# Save Folium map to HTML
folium_map_path = os.path.join(inputDir, "map.html")
m.save(folium_map_path)

# Create a timeline plot using Plotly
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

# Add a vertical line (time marker) and a slider to control the time marker
time_range = pd.date_range(start=df['start'].min(), end=df['end'].max(), freq='T')

steps = []
for time_point in time_range:
    step = dict(
        method='update',
        args=[{'shapes': [{'type': 'line', 'x0': time_point, 'x1': time_point, 'y0': 0, 'y1': 30, 'line': {'color': 'red', 'width': 2}}]}],
        label=str(time_point)
    )
    steps.append(step)

sliders = [dict(
    active=0,
    pad={"t": 50},
    steps=steps
)]

fig.update_layout(
    sliders=sliders,
    legend=dict(yanchor="bottom", y=0.01),
    margin=dict(l=0, r=0, b=0, t=0),
    autosize=False,
    width=600,
    height=200,
    shapes=[dict(
        type="line",
        x0=time_range[0],
        x1=time_range[0],
        y0=0,
        y1=30,
        line=dict(color="red", width=2)
    )]
)

plotly_timeline_html = fig.to_html(full_html=False, div_id='plotly_div')

# Read the Folium map HTML content
with open(folium_map_path, 'r') as f:
    folium_map_html = f.read()

# Combine both HTMLs into a single file
combined_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <title>Swamp ARU Analysis</title>
    <style>
        body {{ margin: 0; padding: 0; }}
        #plotly_div {{ height: 50%; }}
        #map_div {{ height: 50%; }}
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/leaflet.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/leaflet.css" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet-timedimension/1.1.0/leaflet.timedimension.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet-timedimension/1.1.0/leaflet.timedimension.control.min.css" />
</head>
<body>
    <div id="plotly_div">{plotly_timeline_html}</div>
    <div id="map_div">{folium_map_html}</div>
</body>
</html>
"""

# Save the combined HTML to a file
combined_html_path = os.path.join(inputDir, "combined_output_folium.html")
with open(combined_html_path, 'w') as f:
    f.write(combined_html)

print(f"Combined output saved to {combined_html_path}")
