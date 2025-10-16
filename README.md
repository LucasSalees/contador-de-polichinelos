# Contador de Polichinelos com Visão Computacional 🏋️‍♂️

![Badge Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![Badge OpenCV](https://img.shields.io/badge/OpenCV-4.5-blue?logo=opencv)
![Badge MediaPipe](https://img.shields.io/badge/MediaPipe-0.8-orange)

Este projeto é uma aplicação em Python que utiliza a webcam para detectar e contar o número de polichinelos (jumping jacks) realizados por uma pessoa em tempo real, usando técnicas de visão computacional e estimativa de pose.

## 📝 Descrição

O sistema captura o vídeo da webcam, processa cada quadro para identificar os pontos-chave do corpo humano (como ombros, cotovelos, quadris e joelhos) e, com base na posição desses pontos, determina se um polichinelo completo foi realizado. Um contador na tela exibe o número de repetições em tempo real.

## ✨ Funcionalidades

- **Detecção de Pose em Tempo Real**: Utiliza a biblioteca MediaPipe do Google para identificar 33 pontos corporais (landmarks).
- **Contagem de Repetições**: Algoritmo para calcular os ângulos dos membros e determinar os estágios do movimento (braços/pernas abertos vs. fechados).
- **Feedback Visual**: Exibe o vídeo da câmera com os pontos corporais desenhados e um contador de repetições na tela.
- **Fácil de Usar**: Basta executar o script e começar a se exercitar em frente à câmera.

##  демонстрация (Demonstração)

*(Sugestão: Grave um GIF rápido do programa funcionando e coloque aqui para um resultado mais profissional!)*

![Demonstração do Projeto](https://i.imgur.com/link_para_seu_gif.gif)

## 🛠️ Tecnologias Utilizadas

- **Python**: Linguagem principal do projeto.
- **OpenCV**: Para captura e manipulação de vídeo da webcam.
- **MediaPipe**: Para a detecção de pontos corporais (pose estimation) de alta fidelidade.

## 🚀 Como Executar o Projeto

Siga os passos abaixo para configurar e rodar o projeto em sua máquina local.

### Pré-requisitos

- Python 3.8 ou superior
- Uma webcam conectada ao computador

### Instalação

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/LucasSalees/contador-de-polichinelos.git](https://github.com/LucasSalees/contador-de-polichinelos.git)
    ```
    *(Observação: altere `contador-de-polichinelos` se o nome do seu repositório no GitHub for diferente)*

2.  **Navegue até a pasta do projeto:**
    ```bash
    cd contador-de-polichinelos
    ```

3.  **(Recomendado) Crie e ative um ambiente virtual:**
    ```bash
    # Criar o ambiente
    python -m venv venv

    # Ativar no Windows
    .\venv\Scripts\activate

    # Ativar no Linux/macOS
    source venv/bin/activate
    ```

4.  **Instale as dependências a partir do arquivo `requirements.txt`:**
    ```bash
    pip install -r requirements.txt
    ```

### Execução

Com o ambiente virtual ativado, execute o script principal:
```bash
python system.py
```
Uma janela com a imagem da sua webcam aparecerá. Posicione-se de forma que seu corpo inteiro seja visível e comece a fazer os polichinelos. O contador será atualizado na tela.

## 🔧 Como Funciona

1.  **Captura de Vídeo**: O OpenCV é usado para acessar a webcam e capturar os quadros de vídeo.
2.  **Detecção de Pontos Corporais**: Cada quadro é enviado para o modelo de `Pose` do MediaPipe, que retorna a localização dos 33 pontos corporais.
3.  **Cálculo de Ângulos**: O código extrai as coordenadas de pontos específicos (como ombros, cotovelos e quadris) para calcular os ângulos dos braços e pernas.
4.  **Lógica de Contagem**: Uma máquina de estados simples verifica se o corpo passou do estado "fechado" (braços para baixo) para o estado "aberto" (braços para cima) e vice-versa. Uma repetição completa é contada quando essa sequência ocorre.
5.  **Exibição**: O OpenCV é usado para desenhar os pontos corporais, as linhas de conexão e o contador de volta no quadro de vídeo, que é então exibido na tela.

---

Feito por **Lucas Sales - Lucas Rossi - Giovanni Grecchi**

[![LinkedIn](https://img.shields.io/badge/linkedin-%230077B5.svg?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/lucas-salees/)
[![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)](https://github.com/LucasSalees)