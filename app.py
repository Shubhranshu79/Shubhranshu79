# app.py - wrapper to run Prototype.py as Streamlit entrypoint
import runpy, os

runpy.run_path(
    os.path.join(os.path.dirname(__file__), "Prototype.py"),
    run_name="__main__"
)
