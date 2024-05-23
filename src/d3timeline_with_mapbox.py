import os
import datetime
import pandas as pd

# Define input directory and file paths
inputDir = '../data/umich_swamp_aru_analysis/'
filePath = os.path.join(inputDir, "swamp_aru_audio_assets.csv")
recorder_info_path = os.path.join(inputDir, "swamp_aru_recorder_info.csv")

# Read the assets CSV file
assets = pd.read_csv(filePath)

# Prepare datetime strings and convert to milliseconds since 1970-01-01
datetimestrs = []
for row_idx, row in assets.iterrows():
    datetimestrs.append(f"{row['year']} {row['month']} {row['day']} {row['hour']:02d}:{row['minute']:02d}:{row['second']:02d}")

# Create dataframe with start, end, and site information
df = {"start": [], "end": [], "site":[]}
for row_idx, row in assets.iterrows():
    d = datetime.datetime.strptime(datetimestrs[row_idx], "%Y %m %d %H:%M:%S")
    dd = datetime.timedelta(seconds=row['duration'])
    df["site"].append(int(row["site_num"][1:]))
    df["start"].append(int(d.timestamp() * 1000))  # Convert to milliseconds
    df["end"].append(int((d + dd).timestamp() * 1000))  # Convert to milliseconds

df = pd.DataFrame(df)

# Read the recorder info CSV
recorder_info = pd.read_csv(recorder_info_path)

# Merge the recorder info with the asset data
df = pd.merge(df, recorder_info, left_on='site', right_on='site_num')

# Sort the sites numerically
df = df.sort_values(by='site')

# Prepare the data for the HTML template
data = df.to_dict(orient='records')

# Create the HTML template
html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Swamp ARU Analysis</title>
    <script src="https://d3js.org/d3.v6.min.js"></script>
    <script src="https://api.mapbox.com/mapbox-gl-js/v2.6.1/mapbox-gl.js"></script>
    <link href="https://api.mapbox.com/mapbox-gl-js/v2.6.1/mapbox-gl.css" rel="stylesheet" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/d3-simple-slider/1.5.7/d3-simple-slider.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/d3-simple-slider/1.5.7/d3-simple-slider.min.css" rel="stylesheet" />
    <style>
        body {{ margin: 0; padding: 0; }}
        #plot {{ height: 50vh; width: 100%; }}
        #map {{ height: 50vh; width: 100%; }}
        .axis line, .axis path {{
            shape-rendering: crispEdges;
            stroke: black;
        }}
        .marker-number {{
            font-size: 12px;
            color: white;
            text-align: center;
        }}
        .d3-slider {{ 
            margin-left: 50px;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div id="plot"></div>
    <div id="map"></div>

    <script>
        // Data preparation
        const data = {data};

        // Dimensions and margins
        const margin = {{top: 20, right: 20, bottom: 50, left: 50}},
              width = window.innerWidth - margin.left - margin.right,
              height = 250 - margin.top - margin.bottom;

        // Create scales
        const x = d3.scaleTime()
            .domain([d3.min(data, d => d.start), d3.max(data, d => d.end)])
            .range([0, width]);

        const y = d3.scaleBand()
            .domain(data.map(d => d.site))
            .range([height, 0])
            .padding(0.1);

        // Create SVG for Cleveland plot
        const svg = d3.select("#plot").append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
          .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        // Add X axis
        svg.append("g")
            .attr("transform", "translate(0," + height + ")")
            .call(d3.axisBottom(x));

        // Add Y axis
        svg.append("g")
            .call(d3.axisLeft(y));

        // Add lines
        svg.selectAll("line")
          .data(data)
          .enter().append("line")
            .attr("x1", d => x(d.start))
            .attr("x2", d => x(d.end))
            .attr("y1", d => y(d.site) + y.bandwidth() / 2)
            .attr("y2", d => y(d.site) + y.bandwidth() / 2)
            .attr("stroke", "black")
            .attr("stroke-width", 2);

        // Add a vertical time marker
        const timeMarker = svg.append("line")
            .attr("stroke", "red")
            .attr("stroke-width", 2)
            .attr("y1", 0)
            .attr("y2", height);

        // Initialize Mapbox
        mapboxgl.accessToken = 'pk.eyJ1IjoiamtlbmRhbGxiYXIiLCJhIjoiY2x3aXJtdndlMHQ2ODJpbGV2MHZuczJ6ZSJ9.Osr0UL8698r-LhyuBIXSog';
        const map = new mapboxgl.Map({{
            container: 'map',
            style: 'mapbox://styles/mapbox/satellite-v9'
        }});

        // Define bounds
        const bounds = new mapboxgl.LngLatBounds();

        // Add markers
        data.forEach(d => {{
            const el = document.createElement('div');
            el.className = 'marker-number';
            el.style.backgroundColor = 'rgba(0, 123, 255, 0.9)';
            el.style.borderRadius = '50%';
            el.style.width = '30px';
            el.style.height = '30px';
            el.innerText = d.site;
            el.style.display = 'flex';
            el.style.alignItems = 'center';
            el.style.justifyContent = 'center';

            const marker = new mapboxgl.Marker(el)
                .setLngLat([d.longitude, d.latitude])
                .setPopup(new mapboxgl.Popup().setText('Site: ' + d.site))
                .addTo(map);
            d.marker = marker;
            
            // Extend the bounds to include each marker's position
            bounds.extend([d.longitude, d.latitude]);
        }});

        // Fit the map to the bounds with a specified padding
        map.fitBounds(bounds, {{ padding: 25 }});

        // Create a time slider
        const slider = d3.sliderBottom()
            .min(d3.min(data, d => d.start))
            .max(d3.max(data, d => d.end))
            .step(1000 * 60)
            .width(width - 100)
            .tickFormat(d3.timeFormat('%Y-%m-%d %H:%M'))
            .on('onchange', val => {{
                timeMarker.attr("x1", x(val)).attr("x2", x(val));

                data.forEach(d => {{
                    if (val >= d.start && val <= d.end) {{
                        d.marker.getElement().style.display = 'block';
                    }} else {{
                        d.marker.getElement().style.display = 'none';
                    }}
                }});
            }});

        const gSlider = d3.select("body")
          .append("div")
            .attr("class", "d3-slider")
          .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", 100)
          .append("g")
            .attr("transform", "translate(" + margin.left + "," + 20 + ")");

        gSlider.call(slider);
    </script>
</body>
</html>
"""

# Save the combined HTML to a file
combined_html_path = os.path.join(inputDir, "combined_output.html")
with open(combined_html_path, 'w') as f:
    f.write(html_template)

print(f"Combined output saved to {combined_html_path}")
