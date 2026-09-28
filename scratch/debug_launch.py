import sys
import os

PROJECT_ROOT = r"c:\Users\Neeraj\Desktop\Naya"
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

try:
    from PyQt5.QtWidgets import QApplication
    import omni_floating_widget
    print("Imports OK!")
    app = QApplication.instance() or QApplication(sys.argv)
    print("App created!")
    orb = omni_floating_widget.AxiomFloatingOrb()
    print("Orb instantiated!")
    orb.show()
    print(f"Orb shown! Pos: {orb.pos()}, Size: {orb.size()}, Visible: {orb.isVisible()}")
except Exception as e:
    import traceback
    traceback.print_exc()
