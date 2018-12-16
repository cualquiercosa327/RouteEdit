import PointWidget
import RouteWidget
import SarcLib
import yaz0
import sys
from PyQt5 import QtCore, QtGui, QtWidgets

Qt = QtCore.Qt
CompYaz0, DecompYaz0 = yaz0.getCompressionMethod()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('RouteEdit NSMBU')
        self.setGeometry(500, 500, 1500, 750)

        self.saveFile = QtWidgets.QAction(QtGui.QIcon('RouteEditData/icons/save.png'), '&Save', self)
        self.saveAsFile = QtWidgets.QAction(QtGui.QIcon('RouteEditData/icons/saveAs.png'), '&Save As', self)
        self.openFile = QtWidgets.QAction(QtGui.QIcon('RouteEditData/icons/folder.png'), '&Open', self)
        self.closeFile = QtWidgets.QAction(QtGui.QIcon('RouteEditData/icons/close.png'), '&Close', self)

        self.editor = EditorTabWidget()
        self.currentFilePath = ''

        self.initUi()

    def initUi(self):
        self.editor.setDisabled(True)

        # setup menu bar
        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('&File')
        toolBar = self.addToolBar('File')

        toolBar.setMovable(False)

        self.openFile.setShortcut('Ctrl+O')
        self.saveFile.setShortcut('Ctrl+S')
        self.saveAsFile.setShortcut('Ctrl+Shift+S')
        self.closeFile.setShortcut('Ctrl+W')

        self.openFile.setStatusTip('Open a file')
        self.saveFile.setStatusTip('Save Changes')
        self.saveAsFile.setStatusTip('Save As')
        self.closeFile.setStatusTip('Close the current file')

        self.openFile.triggered.connect(self.loadSarc)
        self.saveFile.triggered.connect(self.saveSarc)
        self.saveAsFile.triggered.connect(self.saveSarcAs)
        self.closeFile.triggered.connect(self.closeSarc)

        self.saveFile.setDisabled(True)
        self.saveAsFile.setDisabled(True)
        self.closeFile.setDisabled(True)

        fileMenu.addAction(self.openFile)
        fileMenu.addAction(self.saveFile)
        fileMenu.addAction(self.saveAsFile)
        fileMenu.addAction(self.closeFile)

        toolBar.addAction(self.openFile)
        toolBar.addSeparator()
        toolBar.addAction(self.saveFile)
        toolBar.addAction(self.saveAsFile)
        toolBar.addSeparator()
        toolBar.addAction(self.closeFile)

        self.setCentralWidget(self.editor)

    def loadSarc(self):
        fileName = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', '', 'Map files (*.szs)')[0]
        if fileName == '':
            return

        self.currentFilePath = fileName
        self.setWindowTitle('RouteEdit NSMBU - %s' % self.currentFilePath)

        with open(fileName, 'rb') as fileObj:
            data = fileObj.read()

        if data[:4] != b'Yaz0':
            return

        data = DecompYaz0(data)
        if data[:4] != b'SARC':
            return

        archive = SarcLib.SARC_Archive(data)
        archive.load(data)

        self.editor.loadData(archive.contents)

        self.saveFile.setDisabled(False)
        self.saveAsFile.setDisabled(False)
        self.closeFile.setDisabled(False)
        self.editor.setDisabled(False)

    def saveSarc(self):
        arcContents = self.editor.getDataFromWidgets()
        newArchive = SarcLib.SARC_Archive()

        for file in arcContents:
            newArchive.addFile(file)

        outFile = newArchive.save()[0]
        CompYaz0(outFile, self.currentFilePath)

    def saveSarcAs(self):
        fileName = QtWidgets.QFileDialog.getSaveFileName(self, 'Save file', '', 'Map files (*.szs)')[0]
        if fileName == '':
            return

        self.currentFilePath = fileName
        self.saveSarc()
        self.setWindowTitle('RouteEdit NSMBU - %s' % self.currentFilePath)

    def closeSarc(self):
        closeDialog = QtWidgets.QMessageBox
        ret = closeDialog.question(self, '', "Close the current file?", closeDialog.Yes | closeDialog.No)

        if ret == closeDialog.Yes:
            self.editor.closeFile()
            self.editor.setDisabled(True)
            self.saveFile.setDisabled(True)
            self.saveAsFile.setDisabled(True)
            self.closeFile.setDisabled(True)

            self.currentFilePath = ''
            self.setWindowTitle('RouteEdit NSMBU')


class EditorTabWidget(QtWidgets.QTabWidget):
    def __init__(self, parent=None):
        QtWidgets.QTabWidget.__init__(self, parent)

        self.pointEditor = PointWidget.PointEditorWidget()
        self.routeEditor = RouteWidget.RouteEditorWidget()
        self.addTab(self.pointEditor, 'Node Unlocks')
        self.addTab(self.routeEditor, 'Path Settings')

        self.files = []

    def loadData(self, archiveContents):
        self.closeFile()

        pointFiles = []
        routeFiles = []

        for file in archiveContents:
            if file.name[:5] == 'route':
                routeFiles.append(file)
            elif file.name[:5] == 'point':
                pointFiles.append(file)
            else:
                if file.name[-6:] not in [".bfres", ".sharc"] and file.name[-8:] != ".sharcfb":
                    print('Unknown File')
                    print(file.name)
                self.files.append(file)

        self.pointEditor.loadData(pointFiles)
        self.routeEditor.loadData(routeFiles)

    def closeFile(self):
        self.pointEditor.closeData()
        self.routeEditor.closeData()
        self.files = []

    def getDataFromWidgets(self):
        pointFiles = self.pointEditor.getArchiveContents()
        routeFiles = self.routeEditor.getArchiveContents()

        archiveContents = pointFiles + routeFiles + self.files

        return archiveContents


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
