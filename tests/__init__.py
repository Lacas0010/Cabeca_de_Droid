import os
import sys

# Garante que a raiz do repositório esteja no sys.path durante a execução dos testes
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
