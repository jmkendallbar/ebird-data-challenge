# SWAMP - extended dataset for May 11-13, 2017

## Overview
This dataset, “SWAMP - extended dataset for May 11-13, 2017“, contains eBird observations, raw audio from a spatiotemporally overlapping array of autonomous recording units (ARUs), predictions from Merlin sound ID (MSID) about which species are present in those files, as well as expert human-annotated ground truth labels. It was collected/created by an extended team associated with the Cornell Lab of Ornithology, including a bevy of citizen scientists, and includes weather data and other potentially useful metadata as well. The dataset is intended for use in aligning multimodal citizen science datasets, and in piloting analyses using raw, un-thresholded MSID predictions.

## Dataset Description
- **Creators*: Grant Van Horn (University of Massachusetts, Amherst) and Eliot Miller (American Bird Conservancy)
- **Date of Release**: 21 May 2024
- **Version**: 1.0
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0)

## Contents
The dataset includes the following files:
- `audio_wav_22050/`: Directory containing the raw audio files.
  - `S1067SSW05_048K_S01_SWIFT28_20170511_170026Z.wav`: Example file name. 72 files are included in this directory.
- `msid/`: Directory containing Merlin sound ID related outputs.
  - `model_text_labels.txt`: The eBird codes, in 2022 taxonomy, to which the outputs have been filtered.
  - `ebird_freq_api_responses/`: Directory containing results of calls to the eBird frequency API.
    - `2017-5-11.csv`: Example file name. 3 files are included in the directory. Each file contains two columns (species_code and frequency).
  - `predictions/`: Directory containing output from MSID.
    - `S1067SSW05_048K_S01_SWIFT28_20170511_170026Z.npz`: Example file name. 72 files are included in this directory. These are numpy files, where file names correspond to the original audio files.
  - `sliding_window_annotations/`: Directory containing time offsets for expert annotations.
    - `S1067SSW05_048K_S01_SWIFT28_20170513_170027Z.npz`: Example file name. 24 files are included in this directory. These are numpy files, where file names correspond to the original audio files. Note that not all audio files are annotated.
- `eBird_Taxonomy_v2022.csv`: The official eBird 2022 taxonomy file.
- `ssw_hotspot_info.csv`: Locality ID and latitude and longitude information for all eBird hotspots located within the study area.
- `swamp_aru_audio_annotations.csv`: Summarized time and frequency offsets for the expert annotations.
- `swamp_aru_audio_assets.csv`: Date, time, and annotator information associated with the ARUs used in this study.
- `swamp_aru_recorder_info.csv`: Locality information for the ARUs used in this study.
- `swamp_checklists.csv`: eBird checklists from the study area from the same time period as the study.
- `swamp_daily_weather.csv`: Summarized daily weather information from the study area.
- `swamp_hourly_weather.csv`: Detailed hourly weather information from the study area.

## Data Structure
- **Variables/Columns**: Brief description of each column/variable in the dataset.
  - `variable1`: Description of variable1.
  - `variable2`: Description of variable2.
  - ...

## Usage
### Prerequisites
- Python is recommended to parse the numpy files, though reticulate theoretically can be used. Either Python or R can be used to analyze the csv files. Excel or an equivalent may be useful for looking at the raw data.

### Instructions
1. **Download the Dataset**: https://clo-merlin-audio.s3.us-east-1.amazonaws.com/SWAMP/umich_swamp_aru_anaylsis.tar.gz
2. **Loading the Data**: Example code or commands to load the data in various tools/languages.
   - **Python**:
     ```python
     import pandas as pd
     data = pd.read_csv('path/to/data_file1.csv')
     ```
   - **R**:
     ```R
     data <- read.csv('path/to/data_file1.csv')
     ```

### Examples
- Include some basic examples of how to analyze or visualize the data.
  - Example 1: Basic statistical analysis.
  - Example 2: Visualization using a specific tool or library.

## Citation
This dataset itself is likely insufficient for most analyses. If you expand on this by using a larger set of the original data, please cite the relevant sources. These include:
- eBird Primary Reference: Sullivan, B.L., C.L. Wood, M.J. Iliff, R.E. Bonney, D. Fink, and S. Kelling. 2009. eBird: a citizen-based bird observation network in the biological sciences. Biological Conservation 142: 2282-2292.
- SWAMP dataset: https://zenodo.org/records/7018484

## License
This dataset is licensed under the Creative Commons Attribution 4.0 International (CC BY 4.0) license. You are free to share and adapt the material, provided you give appropriate credit.

## Contact
For any questions or issues, please contact:
- **Name**: Eliot Miller
- **Email**: eliot.isaac@gmail.com
- **Organization**: American Bird Conservancy

## Acknowledgments
- The citizen scientists who contributed their valuable eBird records. Expert annotators for their work on the SWAMP dataset.


