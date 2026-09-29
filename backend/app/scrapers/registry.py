"""Para adicionar uma farmácia: crie a classe e registre aqui."""
from .html_generic import Ultrafarma
from .official import CmedAnvisa
from .vtex import DrogariaSaoPaulo, Pacheco, PagueMenos

# Drogaraia removida: o site bloqueia acesso automatizado (403 Access Denied).
SCRAPERS = {cls.key: cls for cls in (CmedAnvisa, Ultrafarma, DrogariaSaoPaulo, Pacheco, PagueMenos)}