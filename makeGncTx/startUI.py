###############################################################################################################################
# coding=utf-8
#
# startUI.py -- run the UI for the functions
#
# Copyright (c) 2019 Mark Sattolo <epistemik@gmail.com>
#
__author__ = 'Mark Sattolo'
__author_email__ = 'epistemik@gmail.com'
__python_version__ = 3.6
__created__ = '2018'
__updated__ = '2019-10-19'

from sys import argv
from PyQt5.QtWidgets import (QApplication, QComboBox, QVBoxLayout, QHBoxLayout, QGroupBox, QDialog, QFileDialog,
                             QPushButton, QFormLayout, QDialogButtonBox, QLabel, QTextEdit, QCheckBox)
from functools import partial
from parseMonarchCopyRep import *
path.append('/home/marksa/dev/git/Python/Gnucash/createGncTxs/parsePdf')


# constant strings
GNC_SFX:str    = 'gnc'
MON_SFX:str    = 'txt'
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
    # legacy
    FD_COPY  : NO_NEED ,
    TX_COPY  : NO_NEED ,
    PDF      : NO_NEED ,
    TX       : NO_NEED ,
    QTRS     : NO_NEED
}


# noinspection PyAttributeOutsideInit
class MonarchGnucashServices(QDialog):
    def __init__(self):
        super().__init__()
        self._logger = SattoLog(my_color=MAGENTA, do_logging=True)
        self.title = 'Monarch & Gnucash Services'
        self.left = 120
        self.top = 160
        self.width = 600
        self.height = 800
        self.pdf_file = None
        self.mon_file = None
        self.gnc_file = None

        self.init_ui()
        self._log("startUI:MonarchGnucashServices()\nRuntime = {}\n".format(strnow))

    def _log(self, p_msg:object, p_color:str=''):
        if self._logger:
            calling_frame = inspect.currentframe().f_back
            self._logger.print_info(p_msg, p_color, p_frame=calling_frame)

    def _err(self, p_msg:object, err_frame:FrameType):
        if self._logger:
            self._logger.print_info(p_msg, BR_RED, p_frame=err_frame)

    def init_ui(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.create_group_box()

        self.response_box = QTextEdit()
        self.response_box.setReadOnly(True)
        self.response_box.acceptRichText()
        self.response_box.setText('Hello there!')

        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        qvb_layout = QVBoxLayout()
        qvb_layout.addWidget(self.gb_main)
        qvb_layout.addWidget(self.response_box)
        qvb_layout.addWidget(button_box)

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

        self.add_gnc_file_btn()
        layout.addRow(self.gnc_label, self.gnc_file_btn)

        self.cb_mode = QComboBox()
        self.cb_mode.addItems([TEST, SEND])
        self.cb_mode.currentIndexChanged.connect(partial(self.mode_change))
        layout.addRow(QLabel("Mode:"), self.cb_mode)

        self.cb_domain = QComboBox()
        self.cb_domain.addItems([NO_NEED, BOTH, TRADE, PRICE])
        layout.addRow(QLabel("Domain:"), self.cb_domain)

        horiz_box = QGroupBox("Check:")
        horiz_layout = QHBoxLayout()
        self.ch_json = QCheckBox("Save Monarch info to JSON file?")
        self.ch_debug = QCheckBox("Print DEBUG info?")
        horiz_layout.addWidget(self.ch_json)
        horiz_layout.addWidget(self.ch_debug)
        horiz_box.setLayout(horiz_layout)
        layout.addRow(QLabel("Options"), horiz_box)

        self.exe_btn = QPushButton('Go!')
        self.exe_btn.clicked.connect(partial(self.button_click))
        layout.addRow(QLabel("Execute:"), self.exe_btn)

        self.gb_main.setLayout(layout)

    def add_mon_file_btn(self):
        self.mon_btn_title = 'Get ' + MON + ' file'
        self.mon_file_btn  = QPushButton(self.mon_btn_title)
        self.mon_label     = QLabel(MON+FILE_LABEL)
        self.mon_file_btn.clicked.connect(partial(self.open_file_name_dialog, MON))

    def add_gnc_file_btn(self):
        self.gnc_btn_title = 'Get ' + GNC + ' file'
        self.gnc_file_btn  = QPushButton(NO_NEED)
        self.gnc_label     = QLabel(GNC+FILE_LABEL)
        self.gnc_file_btn.clicked.connect(partial(self.open_file_name_dialog, GNC))

    def open_file_name_dialog(self, label:str):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        caption = "Get {} Files".format(label)
        base_filter  = "{} (*.{});;All Files (*)"

        self._log(label)
        if label == MON:
            ffilter = base_filter.format(MON, MON_SFX)
        else: # GNC
            ffilter = base_filter.format(GNC, GNC_SFX)

        file_name, _ = QFileDialog.getOpenFileName(self, caption, "", ffilter, options=options)
        if file_name:
            self._log("\nFile selected: {}".format(file_name), BLUE)
            display_name = file_name.split('/')[-1]
            if label == MON:
                self.mon_file = file_name
                self.mon_file_btn.setText(display_name)
            else: # GNC
                self.gnc_file = file_name
                self.gnc_file_btn.setText(display_name)

    def mode_change(self):
        """Monarch_Copy: need Gnucash file and domain only if in PROD mode"""
        if self.cb_script.currentText() == MON_COPY:
            if self.cb_mode.currentText() == SEND:
                self.gnc_file_btn.setText(self.gnc_btn_title)
                self.cb_domain.setCurrentText(BOTH)
            else:
                self.gnc_file_btn.setText(NO_NEED)
                self.cb_domain.setCurrentText(NO_NEED)

    def button_click(self):
        """prepare the executable and parameters string"""
        self._log("Clicked '{}'.".format(self.exe_btn.text()), CYAN)
        cl_params = []

        mode = self.cb_mode.currentText()
        selected_fxn = self.cb_script.currentText()

        main_fxn = MAIN_FXNS[selected_fxn]
        self._log("Function to run: {}".format(str(main_fxn)), BROWN)

        # check that necessary files have been selected
        if selected_fxn == MON_COPY:
            cl_params.append('-m' + self.mon_file)
            if self.ch_json.isChecked(): cl_params.append('--json')
            if self.ch_debug.isChecked(): cl_params.append('--debug')
            if mode == SEND:
                if self.gnc_file is None:
                    self.response_box.setText('>>> MUST select a Gnucash File!')
                    return
                if self.cb_domain.currentText() == NO_NEED:
                    self.response_box.setText('>>> MUST select a Domain!')
                    return
                cl_params.append('gnc')
                cl_params.append('-f' + self.gnc_file)
                cl_params.append('-t' + self.cb_domain.currentText())

            self._log("Parameters = \n{}".format(json.dumps(cl_params, indent=4)), GREEN)

        if callable(main_fxn):
            self._log('Sending...', MAGENTA)
            response = main_fxn(cl_params)
            reply = {'response': response, 'log': self._logger.get_log()}
        elif main_fxn == NO_NEED:
            # legacy function
            msg = "legacy function: {}".format(main_fxn)
            self._log(msg)
            reply = {'msg': msg}
        else:
            msg = "Problem with main??!! '{}'".format(main_fxn)
            self._err(msg, inspect.currentframe().fback)
            reply = {'log': self._logger.get_log(), 'msg': msg}

        self.response_box.setText(json.dumps(reply, indent=4))


def ui_main():
    app = QApplication(argv)
    dialog = MonarchGnucashServices()
    dialog.show()
    exit(app.exec_())


if __name__ == '__main__':
    ui_main()
