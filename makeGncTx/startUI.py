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
__updated__ = '2019-07-07'

import sys
import json
from PyQt5.QtWidgets import (QApplication, QComboBox, QVBoxLayout, QHBoxLayout, QGroupBox, QDialog, QFileDialog,
                             QPushButton, QFormLayout, QDialogButtonBox, QLabel, QTextEdit, QCheckBox)
from functools import partial
from Configuration import *
from parseMonarchTxRep import mon_tx_rep_main
from parseMonarchQtrRep import mon_qtr_rep_main
from createGnucashTxs import create_gnc_txs_main
from parseMonarchFundsRep import mon_funds_rep_main
from parseMonarchCopyRep import mon_copy_rep_main
sys.path.append('/home/marksa/dev/git/Python/Gnucash/createGncTxs/parsePdf')
from parsePdf import parse_pdf_main


# constant strings
QTRS:str       = MON + ' Quarterly Report'
PDF:str        = MON + ' PDF Report'
TX:str         = MON + ' Txs Report'
GNC_TXS        = 'Create Gnc Txs'
COPY:str       = 'Copy'
FUNDS:str      = 'Funds'
MON_COPY:str   = MON + ' ' + COPY
FD_COPY:str    = MON + ' ' + FUNDS + ' ' + COPY
TX_COPY:str    = MON + ' Tx ' + COPY
GNC_SFX:str    = 'gnc'
MON_SFX:str    = 'txt'
PDF_SFX:str    = 'pdf'
JSON:str       = 'json'
FILE_LABEL:str = ' File:'
NO_NEED:str    = 'NOT NEEDED'

MAIN_FXNS = {
    # with the new format Monarch report, this is now the only script actually needed...
    MON_COPY : mon_copy_rep_main   ,
    # legacy
    GNC_TXS  : create_gnc_txs_main ,
    FD_COPY  : mon_funds_rep_main  ,
    TX_COPY  : mon_tx_rep_main     ,
    PDF      : parse_pdf_main      ,
    TX       : mon_tx_rep_main     ,
    QTRS     : mon_qtr_rep_main
}

NEED_MONARCH_TEXT = [MON_COPY, FD_COPY, TX_COPY, TX, QTRS]
NEED_MONARCH_JSON = [GNC_TXS]
NEED_GNUCASH_FILE = [GNC_TXS, FD_COPY, QTRS] # and also MON_COPY depending on mode


# noinspection PyAttributeOutsideInit
class MonarchGnucashServices(QDialog):
    def __init__(self):
        super().__init__()
        self.dbg = Gnulog(True)
        self.title = 'Monarch & Gnucash Services'
        self.left = 480
        self.top = 160
        self.width = 800
        self.height = 800
        self.pdf_file = None
        self.mon_file = None
        self.gnc_file = None
        self.dbg.print_info("startUI:MonarchGnucashServices()\nRuntime = {}\n".format(strnow), MAGENTA)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.create_group_box()
        # need a horizontal group box to hold two checkboxes: for save_json and debug
        # place horiz group box in main group box between mode & execute 

        self.response_box = QTextEdit()
        self.response_box.setReadOnly(True)
        self.response_box.acceptRichText()
        self.response_box.setText('Hello there!')

        self.button_box = QDialogButtonBox(QDialogButtonBox.Close)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        qvb_layout = QVBoxLayout()
        qvb_layout.addWidget(self.gb_main)
        qvb_layout.addWidget(self.response_box)
        qvb_layout.addWidget(self.button_box)

        self.setLayout(qvb_layout)
        self.show()

    # noinspection PyUnresolvedReferences
    def create_group_box(self):
        self.gb_main = QGroupBox("Parameters:")
        self.layout = QFormLayout()

        self.cb_script = QComboBox()
        self.cb_script.addItems(x for x in MAIN_FXNS)
        self.cb_script.currentIndexChanged.connect(partial(self.script_change))
        self.layout.addRow(QLabel("Script:"), self.cb_script)
        self.script = self.cb_script.currentText()

        self.add_pdf_file_btn()
        self.layout.addRow(self.pdf_label, self.pdf_file_btn)

        self.add_mon_file_btn()
        self.layout.addRow(self.mon_label, self.mon_file_btn)

        self.add_gnc_file_btn()
        self.layout.addRow(self.gnc_label, self.gnc_file_btn)

        self.cb_mode = QComboBox()
        self.cb_mode.addItems([TEST, PROD])
        self.cb_mode.currentIndexChanged.connect(partial(self.mode_change))
        self.layout.addRow(QLabel("Mode:"), self.cb_mode)

        self.horiz_box = QGroupBox("Check:")
        self.horiz_layout = QHBoxLayout()
        self.ch_json = QCheckBox("Save Monarch info to JSON?")
        self.ch_debug = QCheckBox("Print DEBUG info?")
        self.horiz_layout.addWidget(self.ch_json)
        self.horiz_layout.addWidget(self.ch_debug)
        self.horiz_box.setLayout(self.horiz_layout)
        self.layout.addRow(QLabel("Parameters:"), self.horiz_box)

        self.exe_btn = QPushButton('Go!')
        self.exe_btn.clicked.connect(partial(self.button_click))
        self.layout.addRow(QLabel("Execute:"), self.exe_btn)

        self.gb_main.setLayout(self.layout)

    def add_pdf_file_btn(self):
        self.pdf_btn_title = 'Get ' + PDF + ' file'
        self.pdf_file_btn  = QPushButton(NO_NEED)
        self.pdf_label     = QLabel(PDF+FILE_LABEL)
        self.pdf_file_btn.clicked.connect(partial(self.open_file_name_dialog, PDF))

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

    def open_file_name_dialog(self, label):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        base_caption = "Get {} Files"
        base_filter  = "{} (*.{});;All Files (*)"

        if label == PDF:
            self.dbg.print_info(PDF)
            caption = base_caption.format(PDF)
            ffilter = base_filter.format(PDF, PDF_SFX)
        elif label == MON:
            self.dbg.print_info(MON)
            caption = base_caption.format(MON)
            suffix = JSON if self.script in NEED_MONARCH_JSON else MON_SFX
            ffilter = base_filter.format(MON, suffix)
        else: # GNC
            self.dbg.print_info(GNC)
            caption = base_caption.format(GNC)
            ffilter = base_filter.format(GNC, GNC_SFX)

        file_name, _ = QFileDialog.getOpenFileName(self, caption, "", ffilter, options=options)
        if file_name:
            self.dbg.print_info("\nFile selected: {}".format(file_name), BLUE)
            if label == PDF:
                self.pdf_file = file_name
                self.pdf_file_display = file_name.split('/')[-1]
                self.pdf_file_btn.setText(self.pdf_file_display)
            elif label == MON:
                self.mon_file = file_name
                self.mon_file_display = file_name.split('/')[-1]
                self.mon_file_btn.setText(self.mon_file_display)
            else: # GNC
                self.gnc_file = file_name
                self.gnc_file_display = file_name.split('/')[-1]
                self.gnc_file_btn.setText(self.gnc_file_display)

    def mode_change(self):
        """for Monarch_Copy: need for Gnucash file depends on mode"""
        if self.cb_script.currentText() == MON_COPY:
            if self.cb_mode.currentText() == PROD:
                self.gnc_file_btn.setText(self.gnc_btn_title)
            else:
                self.gnc_file_btn.setText(NO_NEED)

    def script_change(self):
        """need for various input files depends on which script is selected"""
        new_script = self.cb_script.currentText()
        self.dbg.print_info("Script changed to: {}.".format(new_script), MAGENTA)

        if new_script != self.script:
            self.mon_file = None
            if new_script == PDF:
                # PDF button ONLY
                self.pdf_file_btn.setText(self.pdf_btn_title)
                self.mon_file_btn.setText(NO_NEED)
                self.gnc_file_btn.setText(NO_NEED)
                self.gnc_file = None
            else:
                # restore proper text for Monarch file button
                self.mon_file_btn.setText(self.mon_btn_title)

                # if need and previous script didn't have, restore proper text for Gnucash file button
                mode = self.cb_mode.currentText()
                if new_script in NEED_GNUCASH_FILE or (mode == PROD and new_script == MON_COPY):
                    self.gnc_file_btn.setText(self.gnc_btn_title)
                else:
                    self.gnc_file_btn.setText(NO_NEED)
                    self.gnc_file = None
                if self.script == PDF:
                    self.pdf_file_btn.setText(NO_NEED)
                    self.pdf_file = None

            self.script = new_script

    def button_click(self):
        """prepare the executable and parameters string"""
        self.dbg.print_info("Clicked '{}'.".format(self.exe_btn.text()), CYAN)

        mode = self.cb_mode.currentText()
        selected_fxn = self.cb_script.currentText()
        save_json = self.ch_json.isChecked()
        do_debug = self.ch_debug.isChecked()

        main_fxn = MAIN_FXNS[selected_fxn]
        self.dbg.print_info("Function to run: {}".format(str(main_fxn)), YELLOW)

        # check that necessary files have been selected
        if selected_fxn == PDF:
            if self.pdf_file is None:
                self.response_box.setText('>>> MUST select a PDF File!')
                return
            cl_params = [self.pdf_file]
        else:
            if self.mon_file is None:
                self.response_box.setText('>>> MUST select a Monarch File!')
                return
            if selected_fxn == TXS or selected_fxn == TX_COPY:
                cl_params = [self.mon_file, mode]
            elif selected_fxn in NEED_GNUCASH_FILE:
                if self.gnc_file is None:
                    self.response_box.setText('>>> MUST select a Gnucash File!')
                    return
                cl_params = [self.mon_file, self.gnc_file, mode]
            else: # MON_COPY
                if mode == PROD and self.gnc_file is None:
                    self.response_box.setText('>>> MUST select a Gnucash File!')
                    return
                cl_params = ['-m' + self.mon_file]
                if mode == PROD: 
                    cl_params.append('--prod')
                    cl_params.append('-g' + self.gnc_file)
                if save_json: cl_params.append('--json')
                if do_debug: cl_params.append('--debug')

        self.dbg.print_info("Parameters = \n{}".format(json.dumps(cl_params, indent=4)), GREEN)

        if selected_fxn != MON_COPY and mode == TEST:
            self.dbg.print_info('TEST mode', GREEN)
            reply = {'mode': 'TEST', 'log': self.dbg.get_log()}
        else:
            if callable(main_fxn):
                self.dbg.print_info('Sending...', MAGENTA)
                response = main_fxn(cl_params)
                reply = {'response': response, 'log': self.dbg.get_log()}
            else:
                msg = "Problem with main??!! '{}'".format(main_fxn)
                self.dbg.print_error(msg)
                reply = {'msg': msg, 'log': self.dbg.get_log()}

        self.response_box.setText(json.dumps(reply, indent=4))


# TODO: print debug output to ui screen
def ui_main():
    app = QApplication(sys.argv)
    dialog = MonarchGnucashServices()
    dialog.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    ui_main()
