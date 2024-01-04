import sys
import pandas as pd
from pathlib import Path


######## Define path variables ########
# Get the current folder (where qgis_main.py is located)
current_folder =  Path(__file__).parent.absolute()
output_folder = current_folder / 'outputs'
inputs_folder = current_folder / 'inputs'


print("--------------------------------------------------------------------------------------------")
print("--------------------------------------------------------------------------------------------")
print("Cell/Site KMZ Generator.")
print("Please make sure that 'qgis_styles' folder is created inside 'inputs' and contains the files:")
print(f" \n style_Cells.qml \n style_Sites.qml")


######## Input importing ########
print("Step 1 - Manipulating cell database")
# Cells file name and path
cells_file_name = 'Cells.csv'
cells_file_workspace = inputs_folder / cells_file_name
# Sites file name and path
sites_file_name = 'Sites.csv'
sites_file_workspace = inputs_folder / sites_file_name
# Read inputs into pandas Dfs
cell_df = pd.read_csv(cells_file_workspace,sep=',',encoding='latin-1')
cell_df.sort_values(by=['Site_ID'], inplace=True)
site_df = pd.read_csv(sites_file_workspace,sep=',',encoding='latin-1')
site_df.sort_values(by=['Site_ID'], inplace=True)

###############################################
### Perform any necessary data manipulation ###
###############################################

cell_df.to_csv(inputs_folder / 'Cells_mod.csv', sep=',',index=False, encoding='latin-1')
site_df.to_csv(inputs_folder / 'Sites_mod.csv', sep=',',index=False, encoding='latin-1')
print("Step 1 was Successfull - Manipulated cell database stored in 'inputs' folder")


####################################################################################################
######## pyQGIS  ########
print("Step 2 - Starting QGIS application and creating .gpkg files")
# Import basic QGIS packages
from qgis.core import *
from PyQt5.QtWidgets import QApplication
from qgis.gui import QgsMapCanvas
from PyQt5.QtCore import QFileInfo

# Define project path
project_path = str(current_folder)

# Initialize QGIS Application
QgsApplication.setPrefixPath("C:\\Program Files\\QGIS 3.34.0\\apps\\qgis", True)
app = QgsApplication([], True)
app.initQgis()
# Create a canvas instance and project instances
canvas = QgsMapCanvas()
project = QgsProject.instance()

# Add the path to Processing framework
sys.path.append('C:\\Program Files\\QGIS 3.34.0\\apps\\qgis\\python\\plugins')
# Import and initialize Processing framework
from processing.core.Processing import Processing
Processing.initialize()
import processing
# Import KmlTools packages
from kmltools import exportKmz
from kmltools.settings import settings
# Import ShapeTools packages
from shapetools import createPie as pieWedge


###### Part 1 - Create layers  ######
#Load Sites into project
uri = "file:" + str(inputs_folder) + "\\Sites_mod.csv?encoding=%s&delimiter=%s&xField=%s&yField=%s&crs=%s" % ("UTF-8",",", "Longitude", "Latitude","epsg:4326")
#Make a vector layer
site_layer = QgsVectorLayer(uri,"Sites_for_GE","delimitedtext")
#Check if layer is valid
if not site_layer.isValid():
    print ("Issue to load site layer into project")
#Add CSV data    
project.addMapLayer(site_layer)
#Apply style
site_layer.loadNamedStyle(str(inputs_folder) + '\\qgis_styles\\style_Sites.qml')

#Load Cells into project
uri = "file:" + str(inputs_folder) + "\\Cells_mod.csv?encoding=%s&delimiter=%s&xField=%s&yField=%s&crs=%s" % ("UTF-8",",", "Longitude", "Latitude","epsg:4326")
#Make a vector layer
cell_layer = QgsVectorLayer(uri,"Cells_for_GE","delimitedtext")
#Check if layer is valid
if not cell_layer.isValid():
    print ("Issue to load cell layer into project")
#Add CSV data    
project.addMapLayer(cell_layer)

#### Generate petals for CellFile ####
# Use ShapeTools algorithm to draw the petals
layer_str = 'Cells_for_GE'
layer = project.mapLayersByName(layer_str)[0]
petals_output_path = project_path + '\\outputs\\Cells_Polygons.gpkg'

# Instance of shapeTools algorithm
pieAlgo = pieWedge.CreatePieAlgorithm()

# Define the config parameters
params = {'INPUT': layer_str,
          'Azimuth1': QgsProperty.fromExpression('"Azimuth"'),
          'Azimuth2': 60,
          'Radius':200,
          'UnitsOfMeasure': 1,
          'DrawingSegments': 20,
          'OUTPUT': petals_output_path
          }
          
# Initialize a context
context = QgsProcessingContext()
context.setProject(project)
feedback = QgsProcessingFeedback()
context.setFeedback(feedback)

# Initialize parameters and algorithm
pieAlgo.initParameters()
pieAlgo.initAlgorithm()

# Prepare and run algorithm
pieAlgo.prepareAlgorithm( params, context, feedback)
pieAlgo.processAlgorithm( params, context, feedback)

#Load CellFile with petals
sec_layer = QgsVectorLayer(petals_output_path, "cellFile", "ogr")
if not sec_layer.isValid():
    print("Petal cell layer failed to load!")
else:
    QgsProject.instance().addMapLayer(sec_layer)

#Apply style
sec_layer.loadNamedStyle(str(inputs_folder) + '\\qgis_styles\\style_Cells.qml')
project.addMapLayer(sec_layer)

#Package Layers Processing Algorithm
processing.run("native:package", {'LAYERS':[site_layer],'OUTPUT':project_path + '\\outputs\\Sites_for_GE.gpkg','OVERWRITE':False,'SAVE_STYLES':True,'SAVE_METADATA':False,'SELECTED_FEATURES_ONLY':False})                                       
#Package Layers Processing Algorithm
processing.run("native:package", {'LAYERS':[cell_layer,sec_layer],'OUTPUT':project_path + '\\outputs\\Cells_for_GE.gpkg','OVERWRITE':False,'SAVE_STYLES':True,'SAVE_METADATA':False,'SELECTED_FEATURES_ONLY':False})                                       

print("Step 2 was Successfull - generated .gpkg files stored in 'outputs' folder")

###### Part 3 - Export KMZ files  ######
print("Step 3 - Exporting KMZ Files")
# Adjust canvas parameter to avoid errors when running the algorithm
settings.canvas = canvas
# Instance of exportKMZ class
exportKMZ = exportKmz.ExportKmzAlgorithm()

# Initialize a context
context = QgsProcessingContext()
context.setProject(project)
# Initialize and set a feedback
feedback = QgsProcessingFeedback()
context.setFeedback(feedback)

### Part 3.1 - Site layer export ###
# Define layer to be exported
layer_str = 'Sites_for_GE'
layer = site_layer
# Define label fiels
name_field = 'Site_ID'
# Define in case want to use a standard icon 
google_icon = ''
# Map fields  
field_list = [f.name() for f in layer.fields()]
#cols_to_remove = ('code','clutter_code','scale')
#field_list = [e for e in field_list if e not in cols_to_remove]

# Specify output path and name
output_path = project_path + '\\outputs\\' + layer_str +'.kmz'

# Define the config parameters dict
params = {'InputLayer': layer_str,
            'OutputKmz': output_path,
            'NameField':name_field,
            #'UseGoogleIcon': google_icon,
            'DescriptionField': field_list
        }

# Initialize algorithm
exportKMZ.initAlgorithm(params)

# Finally run the algorithm to export layers
exportKMZ.processAlgorithm( params, context, feedback)
print (' KMZ file Successfully Generated for: ' + layer_str)


### Part 3.2 - Cell export  ###
# Define layer to be exported
layer_str = 'cellFile'
layer = sec_layer
# Define label fiels
name_field = 'Site_ID'
# Define in case want to use a standard icon 
google_icon = ''
# Map fields and filter out unecessary ones 
field_list = [f.name() for f in layer.fields()]
#cols_to_remove = ('Unique_Key', 'Radius_[m]','label','color_key','Azimuth plot','clutter_code','scale')
#field_list = [e for e in field_list if e not in cols_to_remove]
label_name = 'Cells_for_GE'
# Specify output path and name
output_path = project_path + '\\outputs\\' + label_name +'.kmz'

# Define the config parameters dict
params = {'InputLayer': layer_str,
        'OutputKmz': output_path,
        'NameField':name_field,
        #'UseGoogleIcon': google_icon,
        'DescriptionField': field_list
        }

# Initialize algorithm
exportKMZ.initAlgorithm(params)

# Finally run the algorithm to export layers
exportKMZ.processAlgorithm( params, context, feedback)
print (' KMZ file Successfully Generated for: ' + label_name)
print("Step 3 was Successfull - All KMZ files stored into 'outputs' folder")
print("Congratulations! The program ran with no issues!")
