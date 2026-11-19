from pathlib import Path
from typing import Dict, List, Optional, Union

import pygame


PASTA_IMAGENS_MONSTROS = (
    Path(__file__).resolve().parents[2] / "prites" / "mosntros"
)
EXTENSOES_IMAGEM = {".png", ".jpg", ".jpeg", ".bmp"}
GRADE_MONSTROS = {"tatu": (2, 2), "rato": (2, 2), "lagartixa": (1, 4)}
GRADE_ATAQUE_MONSTROS = {
    "tatu": (1, 3),
    "rato": (1, 3),
    "lagartixa": (1, 3),
}


def carregar_imagens_monstros(
    pasta: Optional[Union[str, Path]] = None,
) -> Dict[str, pygame.Surface]:
    """Carrega as imagens de monstros e retorna um dicionário pelo nome do arquivo."""
    pasta_imagens = Path(pasta) if pasta is not None else PASTA_IMAGENS_MONSTROS
    if not pasta_imagens.is_dir():
        raise FileNotFoundError(f"Pasta de imagens dos monstros não encontrada: {pasta_imagens}")

    arquivos = sorted(
        arquivo
        for arquivo in pasta_imagens.iterdir()
        if arquivo.is_file() and arquivo.suffix.lower() in EXTENSOES_IMAGEM
    )
    if not arquivos:
        raise FileNotFoundError(
            f"Nenhuma imagem de monstro encontrada em: {pasta_imagens}"
        )

    imagens = {}
    for arquivo in arquivos:
        if arquivo.stem in imagens:
            raise ValueError(f"Mais de uma imagem encontrada para o monstro: {arquivo.stem}")
        imagens[arquivo.stem] = pygame.image.load(str(arquivo))

    return imagens


def separar_spritesheet(
    imagem: pygame.Surface, linhas: int = 2, colunas: int = 2
) -> List[pygame.Surface]:
    if linhas <= 0 or colunas <= 0:
        raise ValueError("A quantidade de linhas e colunas deve ser positiva.")

    largura, altura = imagem.get_size()
    if largura < colunas or altura < linhas:
        raise ValueError("A imagem é pequena demais para a divisão solicitada.")

    quadros = []
    for linha in range(linhas):
        topo = linha * altura // linhas
        base = (linha + 1) * altura // linhas
        for coluna in range(colunas):
            esquerda = coluna * largura // colunas
            direita = (coluna + 1) * largura // colunas
            quadro = imagem.subsurface(
                (esquerda, topo, direita - esquerda, base - topo)
            ).copy()
            limites = quadro.get_bounding_rect()
            if limites.width == 0 or limites.height == 0:
                raise ValueError("O spritesheet contém um quadro vazio.")
            quadros.append(quadro.subsurface(limites).copy())

    return quadros