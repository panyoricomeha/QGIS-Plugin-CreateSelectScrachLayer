from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from .resources_rc import *
from qgis.core import QgsWkbTypes, QgsVectorLayer, QgsFeature, QgsProject
import os.path


class CreateSelectScrachLayer:

    def __init__(self, iface):

        # Reference to QGIS interface
        self.iface = iface

        # Initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # Initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            f'CreateSelectScrachLayer_{locale}.qm'
        )

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Create Select Scratch Layer')
        self.toolbar = self.iface.addToolBar(u'CreateSelectScrachLayer')
        self.toolbar.setObjectName(u'CreateSelectScrachLayer')

        self.pluginIsActive = False
        self.dockwidget = None

    def tr(self, message):
        """Translation helper."""
        return QCoreApplication.translate('CreateSelectScrachLayer', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):


        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip:
            action.setStatusTip(status_tip)
        if whats_this:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)
        return action

    def initGui(self):
        icon_path = ':/plugins/CreateSelectScrachLayer/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Create Select Scratch Layer'),
            callback=self.createScratchLayerFromSelection,
            parent=self.iface.mainWindow()
        )

    def onClosePlugin(self):
        self.pluginIsActive = False

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar

    def createScratchLayerFromSelection(self):

        layer = self.iface.activeLayer()
        if not self.pluginIsActive:
            self.pluginIsActive = True

        # No active vector layer or no selected features
        if not layer or not layer.selectedFeatureCount():
            QMessageBox.warning(
                self.iface.mainWindow(),
                "Warning",
                "Please select a vector layer with selected features."
            )
            return

        # Get selected features
        selected_features = layer.selectedFeatures()

        # Create a scratch layer (same geometry type & CRS)
        geometry_type = QgsWkbTypes.displayString(layer.wkbType())
        crs = layer.crs().authid()
        scratch_layer = QgsVectorLayer(
            f"{geometry_type}?crs={crs}",
            "Selected Features Layer",
            "memory"
        )

        # Copy attribute definitions
        provider = scratch_layer.dataProvider()
        provider.addAttributes(layer.fields())
        scratch_layer.updateFields()

        # Copy selected features
        new_features = []
        for feature in selected_features:
            new_feature = QgsFeature()
            new_feature.setGeometry(feature.geometry())
            new_feature.setAttributes(feature.attributes())
            new_features.append(new_feature)

        # Add features to scratch layer
        provider.addFeatures(new_features)
        scratch_layer.updateExtents()

        # Add to project
        QgsProject.instance().addMapLayer(scratch_layer)

        QMessageBox.information(
            self.iface.mainWindow(),
            "Completed",
            f"{len(new_features)} feature(s) added to the new layer."
        )
