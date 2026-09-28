import sys
import os

PROJECT_ROOT = r"c:\Users\Neeraj\Desktop\Naya"
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
import omni_floating_widget

def run_for_a_bit():
    print("Main runner check...")
    try:
        app = QApplication.instance() or QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)

        orb = omni_floating_widget.AxiomFloatingOrb()
        orb.show()
        print(f"Orb isVisible: {orb.isVisible()}, pos={orb.pos()}")

        QTimer.singleShot(2000, lambda: (print("Closing test..."), app.quit()))
        app.exec_()
        print("Loop completed cleanly!")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_for_a_bit()
