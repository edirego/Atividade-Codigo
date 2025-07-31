# Importa os módulos necessários
from flask import Flask, render_template, request  # Flask: para criar o servidor e renderizar o HTML
import requests  # Para enviar requisições HTTP (usado para conversar com a LLM local)
import subprocess  # Para executar o código JavaScript usando Node.js
import re  # Para usar expressões regulares e extrair o código gerado da resposta

# Inicializa o aplicativo Flask
app = Flask(__name__)

# Configurações da API da LLM (Ollama)
OLLAMA_URL = "http://localhost:11434/api/generate"  # URL da API local do Ollama
MODEL_NAME = "deepseek-coder"  # Nome do modelo a ser utilizado
ARQUIVO_JS = "gerado.js"  # Nome do arquivo onde o código gerado será salvo

# Função que envia o prompt para a LLM e recebe o código de volta
def gerar_codigo(prompt):
    payload = {
        "model": MODEL_NAME,  # Modelo especificado
        "prompt": prompt,     # Texto que será enviado como instrução
        "stream": False       # Indica que não queremos streaming na resposta
    }
    resposta = requests.post(OLLAMA_URL, json=payload)  # Envia requisição POST para a API local
    return resposta.json().get("response", "").strip()  # Extrai o campo "response" da resposta JSON

# Função que limpa e salva o código JavaScript em um arquivo
def salvar_arquivo(codigo):
    # 1. Tenta extrair o conteúdo entre os blocos markdown ```javascript ... ```
    match = re.search(r"```(?:javascript)?\s*([\s\S]*?)\s*```", codigo)
    if match:
        codigo_limpo = match.group(1)  # Se encontrar, extrai apenas o conteúdo do código
    else:
        codigo_limpo = codigo  # Se não encontrar, usa o conteúdo inteiro como código

    # 2. Substitui "alert(" por "console.log(", pois alert não funciona no terminal Node.js
    codigo_limpo = codigo_limpo.replace("alert(", "console.log(")

    # Também substitui "print(" por "console.log(", caso o modelo gere código Python por engano
    codigo_limpo = codigo_limpo.replace("print(", "console.log(")

    # 3. Se houver blocos de código abertos com "{" e sem "}", fecha automaticamente
    if codigo_limpo.count("{") > codigo_limpo.count("}"):
        codigo_limpo += "\n}"

    # 4. Remove caracteres invisíveis como o BOM (Byte Order Mark)
    codigo_limpo = codigo_limpo.replace('\u200b', '').strip()

    # 5. Salva o código no arquivo "gerado.js"
    with open(ARQUIVO_JS, "w", encoding="utf-8") as f:
        f.write(codigo_limpo)

# Função que executa o código JavaScript salvo e retorna a saída (stdout) e erros (stderr)
def executar_codigo():
    processo = subprocess.run(["node", ARQUIVO_JS], capture_output=True, text=True)
    return processo.stdout.strip(), processo.stderr.strip()  # Retorna a saída e o erro (se houver)

# Rota principal da aplicação web
@app.route("/", methods=["GET", "POST"])
def index():
    # Variáveis para armazenar os dados do formulário e os resultados
    prompt = ""
    codigo = ""
    saida = ""
    erro = ""

    # Se o formulário foi enviado via POST (o botão foi clicado)
    if request.method == "POST":
        prompt = request.form["prompt"]           # Lê o prompt digitado pelo usuário
        codigo = gerar_codigo(prompt)             # Gera o código JavaScript com base no prompt
        salvar_arquivo(codigo)                    # Salva o código gerado em arquivo
        saida, erro = executar_codigo()           # Executa o código e captura saída e erro

    # Renderiza a página HTML com os dados processados
    return render_template("index.html", prompt=prompt, codigo=codigo, saida=saida, erro=erro)

# Executa a aplicação em modo debug
if __name__ == "__main__":
    app.run(debug=True)


