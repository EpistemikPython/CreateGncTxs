###############################################################################################################################
# coding=utf-8
#
# startUI.py -- run the UI for the functions
#
# Copyright (c) 2020 Mark Sattolo <epistemik@gmail.com>
#
__author__ = 'Mark Sattolo'
__author_email__ = 'epistemik@gmail.com'
__created__ = '2018'
__updated__ = '2020-03-22'

from PyQt5.QtWidgets import (QApplication, QComboBox, QVBoxLayout, QHBoxLayout, QGroupBox, QDialog, QFileDialog,
                             QPushButton, QFormLayout, QDialogButtonBox, QLabel, QTextEdit, QCheckBox, QInputDialog)
from PyQt5.QtCore import Qt
from functools import partial
from parseMonarchCopyRep import *

# constant strings
GNC_SFX:str    = 'gnc'
MON_SFX:str    = 'monarch'
FILE_LABEL:str = ' File:'
FUNDS:str      = FUND + 's'
MON_COPY:str   = MON + ' Copy'
LEGACY:str     = 'LEGACY'
FD_COPY:str    = LEGACY
TX_COPY:str    = LEGACY
PDF:str        = LEGACY
TX:str         = LEGACY
QTRS:str       = LEGACY
GNC_TXS        = LEGACY
NO_NEED:str    = 'NOT NEEDED'

MAIN_FXNS = {
    # with the new format Monarch report, this is now the only script actually needed...
    MON_COPY : mon_copy_rep_main ,
    # LEGACY
    FD_COPY  : NO_NEED ,
    TX_COPY  : NO_NEED ,
    PDF      : NO_NEED ,
    TX       : NO_NEED ,
    QTRS     : NO_NEED
}


# noinspection PyAttributeOutsideInit,PyCallByClass,PyTypeChecker,PyMethodMayBeStatic
class MonarchGnucashServices(QDialog):
    def __init__(self):
        super().__init__(flags=Qt.WindowSystemMenuHint|Qt.WindowTitleHint)
        self.title = 'Monarch & Gnucash Services'
        self.left = 120
        self.top  = 160
        self.width  = 800
        self.height = 800
        self.pdf_file = None
        self.mon_file = None
        self.gnc_file = None

        self.init_ui()
        ui_lgr.info(F"{self.title} Runtime = {run_ts}\n")

    # noinspection PyArgumentList
    def init_ui(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.log_level = lg.INFO

        self.create_group_box()

        self.response_box = QTextEdit()
        self.response_box.setReadOnly(True)
        self.response_box.acceptRichText()
        self.response_box.setText('Hello there!')

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
        self.cb_script.addItems(x for x in MAIN_FXNS)
        layout.addRow(QLabel("Script:"), self.cb_script)

        self.add_mon_file_btn()
        layout.addRow(self.mon_label, self.mon_file_btn)

        self.cb_mode = QComboBox()
        self.cb_mode.addItems([TEST, SEND])
        self.cb_mode.currentIndexChanged.connect(self.mode_change)
        layout.addRow(QLabel("Mode:"), self.cb_mode)

        self.add_gnc_file_btn()
        layout.addRow(self.gnc_label, self.gnc_file_btn)

        self.cb_domain = QComboBox()
        self.cb_domain.addItems([NO_NEED, BOTH, TRADE, PRICE])
        layout.addRow(QLabel("Domain:"), self.cb_domain)

        horiz_box = QGroupBox("Check:")
        horiz_layout = QHBoxLayout()

        self.chbx_json = QCheckBox("Save Monarch info to JSON file?")
        self.pb_logging = QPushButton("Change the logging level?")
        self.pb_logging.clicked.connect(self.get_log_level)
        # self.chbx_debug = QCheckBox("Print DEBUG info?")

        horiz_layout.addWidget(self.chbx_json, alignment=Qt.AlignAbsolute)
        horiz_layout.addWidget(self.pb_logging, alignment=Qt.AlignAbsolute)
        horiz_box.setLayout(horiz_layout)
        layout.addRow(QLabel("Options"), horiz_box)

        self.exe_btn = QPushButton('Go!')
        self.exe_btn.clicked.connect(self.button_click)
        layout.addRow(QLabel("Execute:"), self.exe_btn)

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

    def open_file_name_dialog(self, label:str):
        f_options = QFileDialog.Options()
        f_options |= QFileDialog.DontUseNativeDialog
        f_caption = F"Get {label} Files"
        base_filter  = "{} (*.{});;All Files (*)"

        ui_lgr.info(label)
        if label == MON:
            f_filter = base_filter.format(MON, MON_SFX)
        else: # GNC
            f_filter = base_filter.format(GNC, GNC_SFX)

        file_name, _ = QFileDialog.getOpenFileName(self, caption=f_caption, filter=f_filter, options=f_options)
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
        """Monarch_Copy: need Gnucash file and domain only if in SEND mode"""
        if self.cb_script.currentText() == MON_COPY:
            if self.cb_mode.currentText() == SEND:
                if self.gnc_file is None:
                    self.gnc_file_btn.setText(self.gnc_btn_title)
                self.cb_domain.setCurrentText(BOTH)
            else:
                self.gnc_file_btn.setText(NO_NEED)
                self.gnc_file = None
                self.cb_domain.setCurrentText(NO_NEED)

    def button_click(self):
        """prepare the executable and parameters string"""
        ui_lgr.info(F"Clicked '{self.exe_btn.text()}'.")
        cl_params = []

        mode = self.cb_mode.currentText()
        selected_fxn = self.cb_script.currentText()

        main_fxn = MAIN_FXNS[selected_fxn]
        ui_lgr.info(F"Function to run: {str(main_fxn)}")

        # check that necessary files have been selected
        if selected_fxn == MON_COPY:
            if self.mon_file is None:
                self.response_box.append('>>> MUST select a Monarch File!')
                return
            cl_params.append('-m' + self.mon_file)
            if self.chbx_json.isChecked(): cl_params.append('--json')

            # if self.chbx_debug.isChecked(): cl_params.append('-l'+str(lg.DEBUG))
            cl_params.append('-l'+str(self.log_level))

            if mode == SEND:
                if self.gnc_file is None:
                    self.response_box.append('>>> MUST select a Gnucash File!')
                    return
                if self.cb_domain.currentText() == NO_NEED:
                    self.response_box.append('>>> MUST select a Domain!')
                    return
                cl_params.append('gnc')
                cl_params.append('-f' + self.gnc_file)
                cl_params.append('-t' + self.cb_domain.currentText())

            ui_lgr.info(F"Parameters = \n{json.dumps(cl_params, indent=4)}")

        if callable(main_fxn):
            ui_lgr.info('Calling main function...')
            response = main_fxn(cl_params)
            reply = {'response': response}
        elif main_fxn == NO_NEED:
            # LEGACY function
            msg = F"legacy function: {main_fxn}"
            ui_lgr.info(msg)
            reply = {'msg': msg}
        else:
            msg = F"Problem with main??!! '{main_fxn}'"
            ui_lgr.error(msg)
            reply = {'msg': msg, 'log': saved_log_info}

        self.response_box.setText(json.dumps(reply, indent=4))

    def get_log_level(self):
        num, ok = QInputDialog.getInt(self, "Logging Level", "Enter a value (0-100)", value=self.log_level, min=0, max=100)
        if ok:
            self.log_level = num
            ui_lgr.info(F"logging level changed to {num}.")

# END class MonarchGnucashServices


def ui_main():
    app = QApplication(argv)
    dialog = MonarchGnucashServices()
    dialog.show()
    app.exec_()


if __name__ == '__main__':
    ui_lgr = get_logger(MonarchGnucashServices.__name__)
    ui_main()
    finish_logging(MonarchGnucashServices.__name__)
    exit()
