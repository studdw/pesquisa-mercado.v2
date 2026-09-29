from .html_generic import Ultrafarma
from .vtex import DrogariaSaoPaulo, Pacheco, PagueMenos

# Drogaraia removida: o site bloqueia acesso automatizado (403 Access Denied).
# Para incluir a rede, o caminho é acesso oficial via RaiaDrogasil.
SCRAPERS = {cls.key: cls for cls in (Ultrafarma, DrogariaSaoPaulo, Pacheco, PagueMenos)}