###############################################################################################################################
# coding=utf-8
#
# startUI.py -- run the UI for the functions
#
# Copyright (c) 2018-21 Mark Sattolo <epistemik@gmail.com>

__author__ = "Mark Sattolo"
__author_email__ = "epistemik@gmail.com"
__created__ = "2018"
__updated__ = "2021-02-16"

from PyQt5.QtWidgets import (QApplication, QComboBox, QVBoxLayout, QGroupBox, QDialog, QFileDialog, QLabel,
                             QPushButton, QFormLayout, QDialogButtonBox, QTextEdit, QCheckBox, QInputDialog)
from PyQt5.QtCore import Qt
from functools import partial
from parseMonarchCopyRep import *

# constant strings
FILE_LABEL:str = " File:"
MON_COPY:str   = MON + " Copy"
NO_NEED:str    = "NOT NEEDED"


# noinspection PyAttributeOutsideInit
class MonarchGnucashServices(QDialog):
    def __init__(self):
        super().__init__(flags=Qt.WindowSystemMenuHint|Qt.WindowTitleHint)
        self.title = "Monarch & Gnucash Services UI"
        self.left = 120
        self.top  = 160
        self.width  = 800
        self.height = 800
        self.pdf_file = None
        self.mon_file = None
        self.gnc_file = None

        self.init_ui()
        ui_lgr.info(F"{self.title} Runtime = {run_ts}\n")

    # TODO: better layout of widgets
    def init_ui(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.log_level:int = lg.DEBUG

        self.create_group_box()

        self.response_box = QTextEdit()
        self.response_box.setReadOnly(True)
        self.response_box.acceptRichText()
        self.response_box.setText("Hello there!")

        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        qvb_layout = QVBoxLayout()
        # ?? none of the Alignment flags seem to give the same widget appearance as just leaving out the flag...
        qvb_layout.addWidget(self.gb_main)
        qvb_layout.addWidget(self.response_box)
        qvb_layout.addWidget(button_box, alignment=Qt.AlignAbsolute)

        self.setLayout(qvb_layout)
        self.show()

    # noinspection PyUnresolvedReferences
    def create_group_box(self):
        self.gb_main = QGroupBox("Parameters:")
        layout = QFormLayout()

        self.cb_script = QComboBox()
        self.cb_script.addItems([MON_COPY])
        layout.addRow(QLabel("Script:"), self.cb_script)

        self.add_mon_file_btn()
        layout.addRow(self.mon_label, self.mon_file_btn)

        self.cb_mode = QComboBox()
        self.cb_mode.addItems([TEST, PRICE, TRADE, BOTH])
        self.cb_mode.currentIndexChanged.connect(self.mode_change)
        layout.addRow(QLabel(MODE+':'), self.cb_mode)

        self.add_gnc_file_btn()
        layout.addRow(self.gnc_label, self.gnc_file_btn)

        self.chbx_json = QCheckBox("Save Monarch info to JSON file?")
        layout.addRow(QLabel("Save:"), self.chbx_json)

        self.pb_logging = QPushButton("Change the logging level?")
        self.pb_logging.clicked.connect(self.get_log_level)
        layout.addRow(QLabel("Logging:"), self.pb_logging)

        self.exe_btn = QPushButton('Go!')
        self.exe_btn.clicked.connect(self.button_click)
        layout.addRow(QLabel("EXECUTE:"), self.exe_btn)

        self.gb_main.setLayout(layout)

    def add_mon_file_btn(self):
        self.mon_btn_title = F"Get {MON} file"
        self.mon_file_btn  = QPushButton(self.mon_btn_title)
        self.mon_label     = QLabel(MON+FILE_LABEL)
        self.mon_file_btn.clicked.connect(partial(self.open_file_name_dialog, MON))

    def add_gnc_file_btn(self):
        self.gnc_btn_title = F"Get {GNC} file"
        self.gnc_file_btn  = QPushButton(NO_NEED)
        self.gnc_label     = QLabel(GNC+FILE_LABEL)
        self.gnc_file_btn.clicked.connect(partial(self.open_file_name_dialog, GNC))

    # TODO: accept as input a json file with previously parsed trades and prices
    def open_file_name_dialog(self, label:str):
        f_options = QFileDialog.Options()
        f_options |= QFileDialog.DontUseNativeDialog
        f_caption = F"Get {label} Files"

        ui_lgr.info(label)
        if label == MON:
            f_filter = F"{MON} (*.monarch);;All Files (*)"
            f_dir = "/newdata/dev/git/Python/Gnucash/createGncTxs/makeGncTx/copyMonarch"
        else: # GNC
            f_filter = F"{GNC} (*.gnc *.gnucash);;All Files (*)"
            f_dir = "/newdata/dev/git/Python/Gnucash/app-files"

        file_name, _ = QFileDialog.getOpenFileName(self, caption=f_caption, filter=f_filter, directory=f_dir, options=f_options)
        if file_name:
            ui_lgr.info(F"\nFile selected: {file_name}")
            display_name = file_name.split('/')[-1]
            if label == MON:
                self.mon_file = file_name
                self.mon_file_btn.setText(display_name)
            else: # GNC
                self.gnc_file = file_name
                self.gnc_file_btn.setText(display_name)

    def mode_change(self):
        if self.cb_mode.currentText() == TEST:
            # need Gnucash file and domain only if in SEND mode
            self.gnc_file_btn.setText(NO_NEED)
            self.gnc_file = None
        else:
            if self.gnc_file is None:
                self.gnc_file_btn.setText(self.gnc_btn_title)

    def get_log_level(self):
        num, ok = QInputDialog.getInt(self, "Logging Level", "Enter a value (0-100)", value=self.log_level, min=0, max=100)
        if ok:
            self.log_level = num
            ui_lgr.info(F"logging level changed to {num}.")

    def button_click(self):
        """
        prepare the parameters string and send to parseMonarchCopyRep.main_mon_copy_rep()
        """
        ui_lgr.info(F"Clicked '{self.exe_btn.text()}'.")

        # check that necessary files have been selected
        if self.mon_file is None:
            self.response_box.append(">>> MUST select a Monarch File!")
            return

        cl_params = ['-m' + self.mon_file, '-l' + str(self.log_level)]

        if self.chbx_json.isChecked():
            cl_params.append('--json')

        mode = self.cb_mode.currentText()
        if mode != TEST:
            if self.gnc_file is None:
                self.response_box.append(">>> MUST select a Gnucash File!")
                return
            cl_params.append('gnc')
            cl_params.append('-f' + self.gnc_file)
            cl_params.append('-t' + mode)

        ui_lgr.info(F"Parameters = \n{json.dumps(cl_params, indent=4)}")

        try:
            ui_lgr.info("Calling main_mon_copy_rep...")
            response = main_mon_copy_rep(cl_params)
            reply = {"response": response}
        except Exception as bcce:
            msg = repr(bcce)
            ui_lgr.error(msg)
            reply = {"EXCEPTION" : msg}

        self.response_box.setText(json.dumps(reply, indent=4))

# END class MonarchGnucashServices


def ui_main():
    app = QApplication(argv)
    dialog = MonarchGnucashServices()
    dialog.show()
    app.exec_()


if __name__ == '__main__':
    ui_lgr = get_logger(MonarchGnucashServices.__name__)
    ui_main()
    finish_logging(MonarchGnucashServices.__name__, sfx='gncout')
    exit()
