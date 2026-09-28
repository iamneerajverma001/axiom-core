import sys
import os

PROJECT_ROOT = r"c:\Users\Neeraj\Desktop\Naya"
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
import omni_floating_widget

app = QApplication.instance() or QApplication(sys.argv)
orb = omni_floating_widget.AxiomFloatingOrb()
orb.show()

print(f"Orb created! winId={int(orb.winId())}, isVisible={orb.isVisible()}, geometry={orb.geometry()}")

# Let it process events for 1 second
def quit_test():
    print("Test finished successfully!")
    app.quit()

QTimer.singleShot(1500, quit_test)
app.exec_()
