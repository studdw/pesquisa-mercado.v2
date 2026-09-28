"""Para adicionar uma farmácia: crie a classe (VtexScraper ou HtmlScraper) e registre aqui."""
from .html_generic import DrogaRaia, Ultrafarma
from .vtex import DrogariaSaoPaulo, Pacheco, PagueMenos

SCRAPERS = {cls.key: cls for cls in (Ultrafarma, DrogaRaia, DrogariaSaoPaulo, Pacheco, PagueMenos)}
