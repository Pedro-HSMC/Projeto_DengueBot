from flask import Flask, render_template, request, session
import unicodedata

app = Flask(__name__)
# O session precisa de uma "chave secreta" para funcionar com segurança
app.secret_key = 'chave_super_secreta_denguebot' 

def remover_acentos(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').lower()

def calcular_score_risco(dados):
    score = 0
    if remover_acentos(dados.get("larvas", "")) == "sim":
        score += 50
    if remover_acentos(dados.get("agua_parada", "")) == "sim":
        score += 35
    if remover_acentos(dados.get("local", "")) == "publico":
        score += 15
    return score

def classificar_prioridade(score):
    if score >= 85:
        return "CRÍTICA (Intervenção em até 24h)"
    elif score >= 50:
        return "ALTA (Intervenção em até 48h)"
    elif score >= 35:
        return "MÉDIA (Monitoramento na semana)"
    else:
        return "BAIXA (Planejamento rotineiro)"

@app.route('/', methods=['GET', 'POST'])
def chat():
    # Se o usuário clicar em "Reiniciar", limpamos a memória do chat
    if request.method == 'POST' and request.form.get('escolha') == "Reiniciar":
        session.clear()

    # 1. Configuração inicial (Se a conversa acabou de começar)
    if 'historico' not in session:
        session['historico'] = [
            {"remetente": "bot", "texto": "Olá! Sou o DengueBot v2.0. O foco que você quer relatar está em local público ou privado?"}
        ]
        session['passo'] = 0
        session['respostas'] = {}

    # 2. Processamento do clique do usuário
    if request.method == 'POST' and request.form.get('escolha') != "Reiniciar":
        escolha_usuario = request.form.get('escolha')
        
        # Salva a mensagem do usuário na tela
        session['historico'].append({"remetente": "user", "texto": escolha_usuario})
        session.modified = True
        
        passo_atual = session['passo']

        # Avalia a resposta e define a próxima pergunta
        if passo_atual == 0:
            session['respostas']['local'] = escolha_usuario
            session['historico'].append({"remetente": "bot", "texto": "Há água parada visível no local?"})
            session['passo'] = 1
            
        elif passo_atual == 1:
            session['respostas']['agua_parada'] = escolha_usuario
            session['historico'].append({"remetente": "bot", "texto": "Você consegue ver larvas na água?"})
            session['passo'] = 2
            
        elif passo_atual == 2:
            session['respostas']['larvas'] = escolha_usuario
            
            # Chegamos ao fim, fazemos o cálculo
            score = calcular_score_risco(session['respostas'])
            prioridade = classificar_prioridade(score)
            
            relatorio = (f"📋 <b>RELATÓRIO GERADO</b><br>"
                         f"Pontuação: {score} pontos.<br>"
                         f"Prioridade: {prioridade}.<br>"
                         f"Registro salvo com sucesso.")
            
            session['historico'].append({"remetente": "bot", "texto": relatorio})
            session['passo'] = 3

    # 3. Define quais botões vão aparecer na tela com base no passo atual
    opcoes = []
    if session['passo'] == 0:
        opcoes = ["Público", "Privado"]
    elif session['passo'] == 1 or session['passo'] == 2:
        opcoes = ["Sim", "Não"]
    elif session['passo'] == 3:
        opcoes = ["Reiniciar"]

    # Envia tudo pronto para o HTML
    return render_template('index.html', historico=session['historico'], opcoes=opcoes)

import os

if __name__ == "_main_":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)