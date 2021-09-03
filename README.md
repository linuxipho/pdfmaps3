# pdfmaps3

This script helps you to produce raster maps for Android/iOS App **Avenza Maps**.

## Data sources
You will need a raster data source in a known projection and ideally larger scale datasets to generate the higher tiles levels.
For now, datasets are hard-coded for my personnal use, but easily replaceable.

## Running
You just need to configure the `main.py` file with your data sources, a map name and the map extent.
Then execute `python main.py`, the resulting map will be rendered in `out` folder.