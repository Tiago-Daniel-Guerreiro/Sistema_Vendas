
import sys
import traceback
try:
    from Base import gerarEsquema
    print("Iniciando gerarEsquema...")
    gerarEsquema()
    print("gerarEsquema concluído com sucesso.")
except Exception:
    traceback.print_exc()
