import os
import random
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image


class PDFMap:

    def __init__(self, map_name, xmin, xmax, ymin, ymax, data_dir):
        """Initialisation de la classe"""

        # Désactive la création des fichiers de métadonnées (*.aux.xml)
        os.environ['GDAL_PAM_ENABLED'] = 'NO'
        # Paramètres de la carte à générer
        self.map_name = map_name
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        # Emplacement des jeux de donnés
        self.data_dir = Path(data_dir)
        self.scan25 = self.data_dir / 'SC25_TOUR_TIF_LZW_LAMB93' / 'index.vrt'
        self.scan100 = self.data_dir / 'SC100_TIF_LZW_LAMB93' / 'index.vrt'
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tile_dir = Path(self.tmp_dir.name, 'tiles')
        self.map_file = Path.cwd() / 'out' / f"{self.map_name}.zip"
        Path.mkdir(self.tile_dir)

    def render_level(self, level, scale, dataset, method='near'):
        """Render pdfmaps level according to given parameters"""

        print(f"Render level {level} @ 1:{int(scale*10000)} (1cm <=> {int(scale*100)}m)")

        # Création d'un fichier temporaire
        tmp_file = Path(self.tmp_dir.name) / f"{level}.png"

        # Extraction de la zone au format PNG et rééchantillonnage si demandé
        subprocess.run([
            'gdal_translate', '-of', 'PNG', '-co', 'ZLEVEL=1', '-projwin',
            str(self.xmin), str(self.ymax), str(self.xmax), str(self.ymin),
            '-tr', str(scale), str(scale), '-r', method, str(dataset), tmp_file
        ])

        # Création des tuiles selon le schéma requis par Avenza Maps
        subprocess.run([
            'gdal_retile.py', '-of', 'PNG', '-co', 'ZLEVEL=9', '-targetDir', self.tile_dir, tmp_file
        ])

        # Suppression du fichier temporaire
        tmp_file.unlink()

    def compute_georeference_file(self, level_1_res=5):
        """Create custom georeference file"""

        # On créé une copie du fichier de référencement
        ref_file = Path(self.tmp_dir.name) / f"{self.map_name}.tif.ref"
        shutil.copyfile('lamb93.ref', ref_file)
        # On ouvre le fichier en mode 'ajout'
        with ref_file.open('a') as f:
            # Taille de la carte en pixels pour le niveau 1
            width = int((self.xmax - self.xmin) / level_1_res)
            height = int((self.ymax - self.ymin) / level_1_res)
            # On ajoute à la fin du fichier contenant la projection
            f.write(
                f"{self.xmin},{level_1_res},0,{self.ymax},0,{-level_1_res}"
                f"\n{width},{height}"
            )

    def rename_tiles(self):
        """Rename tiles to required schema"""

        # On itère dans le répertoire des tuiles
        for tile in self.tile_dir.iterdir():
            # Créé une liste des coordonnées
            coords = list(map(int, tile.stem.split('_')))
            # Renomme avec un nouveau séparateur et un index différent
            tile.rename(self.tile_dir / f"{coords[0]}x{coords[1]-1}x{coords[2]-1}.png")

    def make_thumbnail(self):
        """Create thumb from random tile"""

        img = Image.open(random.choice(list(self.tile_dir.glob('2x*.png'))))
        extent = (0, 0, 128, 128)
        thumb = img.crop(extent)
        thumb.save(f'{self.tmp_dir.name}/thumb.png')

    def package_map(self):
        os.chdir(self.tmp_dir.name)
        subprocess.call(['zip', '-q', '-r', '-D', self.map_file, '.', '-i', '*', 'tiles/*'])

    def run(self):
        self.render_level(level=2, scale=2.5, dataset=self.scan25)
        self.render_level(level=1, scale=5, dataset=self.scan25, method='lanczos')
        self.render_level(level=0, scale=10, dataset=self.scan100, method='lanczos')
        self.compute_georeference_file()
        self.rename_tiles()
        self.make_thumbnail()
        self.package_map()


if __name__ == '__main__':

    pdfmap = PDFMap(
        map_name='TestMap',
        xmin=500_000, xmax=520_000, ymin=6_500_000, ymax=6_520_000,
        data_dir='$HOME/SIG/IGN/SCAN')

    pdfmap.run()
