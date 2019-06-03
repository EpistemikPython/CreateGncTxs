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
__updated__ = '2019-06-02'

import sys
import json
from PyQt5.QtWidgets import (QApplication, QComboBox, QVBoxLayout, QGroupBox, QDialog, QFileDialog,
                             QPushButton, QFormLayout, QDialogButtonBox, QLabel, QTextEdit)
from functools import partial
from Configuration import *
from parseMonarchTxRep import mon_tx_rep_main
from parseMonarchQtrRep import mon_qtr_rep_main
from createGnucashTxs import create_gnc_txs_main
sys.path.append('/home/marksa/dev/git/Python/Gnucash/createGncTxs/parsePdf')
from parsePdf import parse_pdf_main


# constant strings
QTRS       = MON + ' Quarterly Report'
PDF        = MON + ' PDF Report'
TX         = MON + ' Txs Report'
GNC_TXS    = 'Create Gnc Txs'
FILE_LABEL = ' File:'
GNC_SFX    = 'gnc'
MON_SFX    = 'txt'
PDF_SFX    = 'pdf'
JSON       = 'json'
NO_NEED    = 'NOT NEEDED'

MAIN_FXNS = {
    GNC_TXS : create_gnc_txs_main ,
    PDF     : parse_pdf_main      ,
    TX      : mon_tx_rep_main     ,
    QTRS    : mon_qtr_rep_main
}


# noinspection PyUnresolvedReferences,PyAttributeOutsideInit
class MonarchGnucashServices(QDialog):
    def __init__(self):
        print_info("startUI:MonarchGnucashServices()\nRuntime = {}\n".format(strnow), MAGENTA)
        super().__init__()
        self.title = 'Monarch & Gnucash Services'
        self.left = 480
        self.top = 160
        self.width = 800
        self.height = 800
        self.pdf_file = None
        self.mon_file = None
        self.gnc_file = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.create_group_box()

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
        self.layout.addRow(QLabel("Mode:"), self.cb_mode)

        self.exe_btn = QPushButton('Go!')
        self.exe_btn.clicked.connect(partial(self.button_click))
        self.layout.addRow(QLabel("Execute:"), self.exe_btn)

        self.gb_main.setLayout(self.layout)

    def add_pdf_file_btn(self):
        self.pdf_btn_title = 'Get ' + PDF + ' file'
        self.pdf_file_btn = QPushButton(NO_NEED)
        self.pdf_label    = QLabel(PDF+FILE_LABEL)
        self.pdf_file_btn.clicked.connect(partial(self.open_file_name_dialog, PDF))

    def add_mon_file_btn(self):
        self.mon_btn_title = 'Get ' + MON + ' file'
        self.mon_file_btn = QPushButton(self.mon_btn_title)
        self.mon_label    = QLabel(MON+FILE_LABEL)
        self.mon_file_btn.clicked.connect(partial(self.open_file_name_dialog, MON))

    def add_gnc_file_btn(self):
        self.gnc_btn_title = 'Get ' + GNC + ' file'
        self.gnc_file_btn = QPushButton(self.gnc_btn_title)
        self.gnc_label    = QLabel(GNC+FILE_LABEL)
        self.gnc_file_btn.clicked.connect(partial(self.open_file_name_dialog, GNC))

    # noinspection PyUnboundLocalVariable
    def open_file_name_dialog(self, label):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        base_caption = "Get {} Files"
        base_filter  = "{} (*.{});;All Files (*)"

        if label == PDF:
            print_info(PDF)
            caption = base_caption.format(PDF)
            ffilter = base_filter.format(PDF, PDF_SFX)
        elif label == MON:
            print_info(MON)
            caption = base_caption.format(MON)
            suffix = MON_SFX if self.script == TX else JSON
            ffilter = base_filter.format(MON, suffix)
        elif label == GNC:
            print_info(GNC)
            caption = base_caption.format(PDF)
            ffilter = base_filter.format(GNC, GNC_SFX)

        file_name, _ = QFileDialog.getOpenFileName(self, caption, "", ffilter, options=options)
        if file_name:
            print_info("\nFile selected: {}".format(file_name), BLUE)
            if label == PDF:
                self.pdf_file = file_name
                self.pdf_file_display = file_name.split('/')[-1]
                self.pdf_file_btn.setText(self.pdf_file_display)
            elif label == MON:
                self.mon_file = file_name
                self.mon_file_display = file_name.split('/')[-1]
                self.mon_file_btn.setText(self.mon_file_display)
            elif label == GNC:
                self.gnc_file = file_name
                self.gnc_file_display = file_name.split('/')[-1]
                self.gnc_file_btn.setText(self.gnc_file_display)

    def script_change(self):
        new_script = self.cb_script.currentText()
        print_info("Script changed to: {}.".format(new_script), MAGENTA)
        if new_script != self.script:
            self.mon_file = None
            if new_script == PDF:
                # PDF button ONLY
                self.pdf_file_btn.setText(self.pdf_btn_title)
                self.mon_file_btn.setText(NO_NEED)
                self.gnc_file_btn.setText(NO_NEED)
                self.gnc_file = None
            else:
                self.mon_file_btn.setText(self.mon_btn_title)
                if self.script == PDF or self.script == TX:
                    self.gnc_file_btn.setText(self.gnc_btn_title)
                    if self.script == PDF:
                        self.pdf_file_btn.setText(NO_NEED)
                        self.pdf_file = None
                    else:
                        self.gnc_file_btn.setText(self.gnc_btn_title)
                if new_script == TX:
                    self.gnc_file_btn.setText(NO_NEED)
                    self.gnc_file = None

            self.script = new_script

    def button_click(self):
        print_info("Clicked '{}'.".format(self.exe_btn.text()), CYAN)
        mode = self.cb_mode.currentText()
        fxn_key = self.cb_script.currentText()

        main_fxn = MAIN_FXNS[fxn_key]
        print_info("Function to run: {}".format(str(main_fxn)), YELLOW)

        if fxn_key == PDF:
            if self.pdf_file is None:
                self.response_box.setText('>>> MUST select a PDF File!')
                return
            cl_params = [self.pdf_file]
        else:
            if self.mon_file is None:
                self.response_box.setText('>>> MUST select a Monarch File!')
                return
            if fxn_key == TX:
                cl_params = [self.mon_file, mode]
            else: # GNC or QTRS
                if self.gnc_file is None:
                    self.response_box.setText('>>> MUST select a Gnucash File!')
                    return
                cl_params = [self.mon_file, self.gnc_file, mode]

        print_info("Parameters = \n{}".format(json.dumps(cl_params, indent=4)), GREEN)

        if mode == TEST:
            print_info('TEST mode', GREEN)
            reply = {'mode': 'TEST', 'log': get_log()}
        else:
            if callable(main_fxn):
                print_info('Sending...', MAGENTA)
                response = main_fxn(cl_params)
                reply = {'response': response, 'log': get_log()}
            else:
                msg = "Problem with main??!! '{}'".format(main_fxn)
                print_error(msg)
                reply = {'msg': msg, 'log': get_log()}

        self.response_box.setText(json.dumps(reply, indent=4))


# TODO: print debug output to ui screen
def ui_main():
    app = QApplication(sys.argv)
    dialog = MonarchGnucashServices()
    dialog.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    ui_main()
