# S_CellSegment_HoVerNet_ROI

Cytomine (https://cytomine.org) app developed by the TIA Centre team (https://warwick.ac.uk/fac/cross_fac/tia/) for Cell/Nuclei detection in region of interests (ROIs),
encapsulating the HoVer-Net code as part of TIAToolbox (https://github.com/TissueImageAnalytics/tiatoolbox) originally developed by Simon Graham et al. as published in Hover-Net: Simultaneous segmentation and classification of nuclei in multi-tissue histology images. Medical Image Analysis, 58, 2019.

This implementation follows Cytomine (=v3.0) external app conventions based on container technology. 
It applies a HoVer-Net pre-trained model (PanNuke) to Cytomine regions of interest within large whole-slide images. 

To launch such an analysis, a user first specify a Cytomine ROI annotation term identifier, a nuclei/cell term identifier, and a list of images where to apply the detector (see screenshot below). The app will then apply the algorithm to all Cytomine ROI annotations labeled by the user with this term, in the list of whole-slide images of the current project. Detected objects are labeled with the nuclei/cell term identifier.

# HoVer-Net weights model

HoVer-Net H&E model downloaded from the link given in https://github.com/vqdang/hover_net.

# Example of HoVer-Net detections in Cytomine web viewer of a whole-slide image
