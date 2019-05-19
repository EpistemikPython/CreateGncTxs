#
# startUI.py -- run the UI for the functions
#
# @author Mark Sattolo <epistemik@gmail.com>
# @version Python 3.6
# @created 2019-05-19
# @updated 2019-05-19

import sys
from PyQt5.QtWidgets import ( QApplication, QComboBox, QVBoxLayout, QGroupBox, QDialog, QFileDialog,
                              QPushButton, QFormLayout, QDialogButtonBox, QLabel, QTextEdit )
from functools import partial
from Configuration import *
sys.path.append('/home/marksa/dev/git/Python/Gnucash/createGncTxs/parsePdf')
from parsePdf import parse_pdf_main
from parseMonarchTxRep import mon_tx_rep_main
from parseMonarchQtrRep import mon_qtr_rep_main
from createGnucashTxs import create_gnc_txs_main


# constant strings
REV_EXPS  = 'Rev & Exps'
ASSETS    = 'Assets'
BALANCE   = 'Balance'
TEST      = 'test'
SEND      = 'send'
QTRS      = 'Quarters'
SHEET_1   = 'Sheet 1'
SHEET_2   = 'Sheet 2'
PDF       = 'Pdf'
TX        = 'Transactions'
GNC       = 'Gnucash'

PARAMS = {
    REV_EXPS  : ['2019', '2018', '2017', '2016', '2015', '2014', '2013', '2012'] ,
    ASSETS    : ['2011', '2010', '2009', '2008'] ,
    BALANCE   : ['today', 'allyears'] ,
    QTRS      : ['0', '1', '2', '3', '4']
}

MAIN_FXNS = {
    PDF   : parse_pdf_main      ,
    TX    : mon_tx_rep_main     ,
    QTRS  : mon_qtr_rep_main    ,
    GNC   : create_gnc_txs_main
}


# noinspection PyAttributeOutsideInit,PyUnresolvedReferences
class CreateGncTxsAndPrices(QDialog):

    def __init__(self):
        super().__init__()
        self.title = 'Gnucash Txs & Prices'
        self.left = 780
        self.top = 160
        self.width = 400
        self.height = 600
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

        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self.gb_main)
        layout.addWidget(self.response_box)
        layout.addWidget(button_box)

        self.setLayout(layout)
        self.show()

    def create_group_box(self):

        self.gb_main = QGroupBox("Parameters:")
        layout = QFormLayout()

        self.cb_script = QComboBox()
        self.cb_script.addItems([REV_EXPS, ASSETS, BALANCE])
        self.cb_script.currentIndexChanged.connect(partial(self.script_change))
        layout.addRow(QLabel("Script:"), self.cb_script)
        self.script = self.cb_script.currentText()

        self.gnc_file_btn = QPushButton('Get Gnucash file')
        self.gnc_file_btn.clicked.connect(partial(self.open_file_name_dialog))
        layout.addRow(QLabel("Gnucash File:"), self.gnc_file_btn)

        self.cb_mode = QComboBox()
        self.cb_mode.addItems([TEST, SEND])
        self.cb_mode.currentIndexChanged.connect(partial(self.mode_change))
        layout.addRow(QLabel("Mode:"), self.cb_mode)
        self.mode = self.cb_mode.currentText()

        self.cb_domain = QComboBox()
        self.cb_domain.addItems(PARAMS[REV_EXPS])
        self.cb_domain.currentIndexChanged.connect(partial(self.selection_change, self.cb_domain))
        layout.addRow(QLabel("Domain:"), self.cb_domain)

        self.cb_qtr = QComboBox()
        self.cb_qtr.addItems(PARAMS[QTRS])
        self.cb_qtr.currentIndexChanged.connect(partial(self.selection_change, self.cb_qtr))
        layout.addRow(QLabel("Quarter:"), self.cb_qtr)

        self.cb_dest = QComboBox()
        self.cb_dest.currentIndexChanged.connect(partial(self.selection_change, self.cb_dest))
        layout.addRow(QLabel("Destination:"), self.cb_dest)

        self.exe_btn = QPushButton('Go!')
        self.exe_btn.clicked.connect(partial(self.button_click))
        layout.addRow(QLabel("Execute:"), self.exe_btn)

        self.gb_main.setLayout(layout)

    def open_file_name_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(self, "Get Gnucash Files", "", "Gnucash Files (*.gnc);;All Files (*)",
                                                   options=options)
        if file_name:
            self.gnc_file = file_name
            self.gnc_file_display = file_name.split('/')[-1]
            self.gnc_file_btn.setText(self.gnc_file_display)

    def script_change(self):
        new_script = self.cb_script.currentText()
        print_info("Script changed to: {}.".format(new_script), MAGENTA)
        if new_script != self.script:
            if new_script == REV_EXPS:
                # adjust Domain
                self.cb_domain.clear()
                self.cb_domain.addItems(PARAMS[REV_EXPS])
                # adjust Quarter if necessary
                if self.script == BALANCE:
                    self.cb_qtr = PARAMS[QTRS]
            elif new_script == ASSETS:
                # adjust Domain
                if self.script == REV_EXPS:
                    self.cb_domain.addItems(PARAMS[ASSETS])
                else: # current script is BALANCE
                    self.cb_domain.clear()
                    self.cb_domain.addItems(PARAMS[REV_EXPS] + PARAMS[ASSETS])
                    # adjust Quarter
                    self.cb_qtr = PARAMS[QTRS]
            elif new_script == BALANCE:
                # adjust Domain
                self.cb_domain.clear()
                self.cb_domain.addItems(PARAMS[BALANCE] + PARAMS[REV_EXPS] + PARAMS[ASSETS])
                # adjust Quarter
                self.cb_qtr.clear()
            else:
                raise Exception("INVALID SCRIPT!!?? '{}'".format(new_script))

            self.script = new_script

    def mode_change(self):
        new_mode = self.cb_mode.currentText()
        print_info("Mode changed to '{}'.".format(new_mode), CYAN)
        if new_mode != self.mode:
            if new_mode == TEST:
                self.cb_dest.clear()
            elif new_mode == SEND:
                self.cb_dest.addItems([SHEET_1, SHEET_2])
            else:
                raise Exception("INVALID MODE!!?? '{}'".format(new_mode))

            self.mode = new_mode

    def button_click(self):
        print_info("Clicked '{}'.".format(self.exe_btn.text()))
        print_info("Script is '{}'.".format(self.cb_script.currentText()))

        if self.gnc_file is None:
            self.response_box.setText('>>> MUST select a Gnucash File!')
            return

        # adjust the mode string if Sheet 1 is the destination
        send_mode = self.cb_mode.currentText()
        if send_mode == SEND:
            if self.cb_dest.currentText() == SHEET_1:
                send_mode += '1'

        cl_params = [self.gnc_file, send_mode, self.cb_domain.currentText(), self.cb_qtr.currentText()]
        print_info(cl_params, GREEN)

        main_fxn = MAIN_FXNS[self.cb_script.currentText()]
        if callable(main_fxn):
            reply = main_fxn(cl_params)
        else:
            msg = "Problem with main??!! '{}'".format(main_fxn)
            print_error(msg)
            reply = msg
        self.response_box.setText(json.dumps(reply, indent=4))

    @staticmethod
    def selection_change(cb):
        print_info("Selection changed to '{}'.".format(cb.currentText()), MAGENTA)


# TODO: print debug output to ui screen
def ui_main():
    app = QApplication(sys.argv)
    dialog = CreateGncTxsAndPrices()
    dialog.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    ui_main()
