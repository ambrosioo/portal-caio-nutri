import os
import json
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from bs4 import BeautifulSoup
from functools import wraps

# --- INICIALIZAÇÃO E CONFIGURAÇÃO DO FLASK ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'uma-chave-secreta-muito-segura-e-dificil'
USER_DB_PATH = 'patients.csv'
PATIENT_DATA_FOLDER = os.path.join(app.instance_path, 'patient_data')
os.makedirs(PATIENT_DATA_FOLDER, exist_ok=True)

# --- CONFIGURAÇÃO DO FLASK-LOGIN ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Por favor, faça o login para acessar esta página."
login_manager.login_message_category = "error"

# --- MODELO DE USUÁRIO ---
class User(UserMixin):
    def __init__(self, id, password, role):
        self.id = id
        self.password = password
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    try:
        users_df = pd.read_csv(USER_DB_PATH)
        user_data = users_df[users_df['username'] == user_id].iloc[0]
        return User(id=user_data['username'], password=user_data['password'], role=user_data['role'])
    except (FileNotFoundError, IndexError):
        return None

def nutritionist_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'nutricionista':
            flash("Acesso não autorizado.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- TEMPLATE HTML ---
HTML_TEMPLATE_CLIENTE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Guia de Consulta Nutricional - {name}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Inter', sans-serif; }}
        .gradient-bg {{ background: linear-gradient(135deg, #1e3a8a, #3b82f6); }}
        ul li {{ margin-bottom: 0.5rem; }}
        .chart-filter-btn.active {{ background-color: #3b82f6; color: white; }}
    </style>
    <script id="patient-data" type="application/json">
        {json_data}
    </script>
</head>
<body class="bg-gray-900 text-gray-200">
    <div class="container mx-auto p-4 sm:p-8">
        <header class="text-center mb-12 p-8 bg-gray-800 border border-gray-700 text-white rounded-2xl shadow-lg">
            <h1 class="text-4xl md:text-5xl font-bold mb-2 text-blue-400">Guia de Consulta Nutricional</h1>
            <p class="text-2xl font-light">{name} - {details}</p>
            <p class="text-sm mt-2 text-gray-400">Data da Consulta: {consultation_date}</p>
        </header>
        <main class="space-y-12">
            <section id="analise">
                <h2 class="text-3xl font-bold mb-6 border-l-4 border-blue-500 pl-4">1. Análise Avançada</h2>
                <div class="grid md:grid-cols-1 lg:grid-cols-3 gap-8">
                    <div class="bg-gray-800 p-6 rounded-2xl shadow-md border border-gray-700 flex flex-col">
                        <h3 class="text-xl font-semibold mb-4 text-blue-400">✅ Análise de Bioimpedância</h3>
                        <ul class="space-y-2 text-gray-300 mb-4">
                            <li><strong>Percentual de Gordura:</strong> <span class="font-bold text-blue-400">{fat_percentage}%</span></li>
                            <li><strong>Massa Muscular:</strong> <span class="font-bold text-blue-400">{muscle_mass} kg</span></li>
                            <li><strong>Água Corporal Total:</strong> <span class="font-bold text-blue-400">{water_percentage}%</span></li>
                            <li><strong>Taxa Metabólica Basal:</strong> <span class="font-bold text-blue-400">{basal_metabolism} kcal</span></li>
                        </ul>
                        {bio_download_button_html}
                    </div>
                    <div class="bg-gray-800 p-6 rounded-2xl shadow-md border border-gray-700">
                        <h3 class="text-xl font-semibold mb-4 text-blue-400">✅ Análise de Hábitos e Rotina</h3>
                        <ul class="space-y-3 text-gray-300">
                            <li><strong>Plano Alimentar:</strong><p class="font-light mt-1">{food_plan_text}</p>
                                {plan_download_button_html}
                            </li>
                            <li><strong>Identificação de Erros:</strong> {errors}</li>
                            <li><strong>Ponto de Melhoria:</strong> {improvements}</li>
                        </ul>
                    </div>
                    <div class="bg-gray-800 p-6 rounded-2xl shadow-md border border-gray-700">
                        <h3 class="text-xl font-semibold mb-4 text-blue-400">✅ Análise de Sinais Corporais</h3>
                        <ul class="space-y-2 list-disc list-inside text-gray-300">{signals_html}</ul>
                    </div>
                </div>
            </section>
            
            <section id="plano-nutricional">
                <h2 class="text-3xl font-bold mb-6 border-l-4 border-blue-500 pl-4">2. Plano Nutricional</h2>
                <div class="grid md:grid-cols-1 lg:grid-cols-3 gap-8">
                    <div class="bg-gray-800 p-6 rounded-2xl shadow-md border border-gray-700">
                        <h3 class="text-xl font-semibold mb-4 text-blue-400">✅ Cardápio 100% Adaptável</h3>
                        <p class="text-gray-400 mb-2">Exemplo de Substituição:</p>
                        <p class="text-gray-300">{substitutions_example}</p>
                    </div>
                    <div class="bg-gray-800 p-6 rounded-2xl shadow-md border border-gray-700">
                        <h3 class="text-xl font-semibold mb-4 text-blue-400">✅ Plano de Suplementação</h3>
                        <ul class="space-y-2 text-gray-300 list-disc list-inside">{supplements_html}</ul>
                    </div>
                    <div class="bg-gray-800 p-6 rounded-2xl shadow-md border border-gray-700">
                        <h3 class="text-xl font-semibold mb-4 text-blue-400">✅ Guia de Compras</h3>
                        <h4 class="font-semibold text-blue-300">Priorizar:</h4>
                        <p class="text-gray-300 mb-2">{shopping_prioritize}</p>
                        <h4 class="font-semibold text-blue-300">Evitar:</h4>
                        <p class="text-gray-300">{shopping_avoid}</p>
                    </div>
                </div>
            </section>

            <section id="acompanhamento">
                <h2 class="text-3xl font-bold mb-6 border-l-4 border-blue-500 pl-4">3. Acompanhamento e Suporte</h2>
                <div class="bg-gray-800 p-8 rounded-2xl shadow-lg grid md:grid-cols-3 gap-8 text-center border border-gray-700">
                    <div>
                        <h3 class="text-xl font-semibold mb-2 text-blue-400">Ajustes em Tempo Real</h3>
                        <p class="text-gray-400">Mande a foto do seu prato e receba feedback em até 12 horas. Adaptação da dieta para viagens e torneios.</p>
                    </div>
                    <div>
                        <h3 class="text-xl font-semibold mb-2 text-blue-400">Monitoramento de Sintomas</h3>
                        <p class="text-gray-400 mb-3">Sentiu inchaço? Reduza o sódio e aumente a ingestão de chás diuréticos. Fale comigo para ajustes.</p>
                        <a href="https://wa.me/5521969489421" target="_blank" class="inline-flex items-center gap-2 text-sm bg-green-500 text-white font-semibold py-2 px-4 rounded-lg hover:bg-green-600 transition-colors">Relatar Sintoma no WhatsApp</a>
                    </div>
                    <div>
                        <h3 class="text-xl font-semibold mb-2 text-blue-400">Suporte por WhatsApp</h3>
                        <p class="text-gray-400">"Posso trocar o frango por peixe?" Respostas rápidas para suas dúvidas do dia a dia.</p>
                    </div>
                </div>
            </section>

            <section id="bonus">
                <h2 class="text-3xl font-bold mb-6 border-l-4 border-blue-500 pl-4">4. Bônus Exclusivos</h2>
                <div class="grid md:grid-cols-3 gap-8">
                    <div class="bg-gray-800 p-6 rounded-2xl text-center shadow-md border border-blue-800 flex flex-col">
                        <h3 class="text-xl font-semibold mb-2 text-blue-400">🎁 E-book de Receitas</h3>
                        <p class="text-blue-300 mb-3">Receitas rápidas e focadas em energia.</p>
                        <a href="https://ambrosioo.github.io/ebook_receitas/" target="_blank" class="mt-auto inline-flex items-center justify-center gap-2 text-sm gradient-bg text-white font-semibold py-2 px-4 rounded-lg">Baixar E-book</a>
                    </div>
                    <div class="bg-gray-800 p-6 rounded-2xl text-center shadow-md border border-blue-800 flex flex-col">
                        <h3 class="text-xl font-semibold mb-2 text-blue-400">🥪 Guia do Fim de Semana</h3>
                        <p class="text-blue-300 mb-3">Lanches inteligentes para não sair do foco.</p>
                        <a href="https://ambrosioo.github.io/guia_fim_de_semana/" target="_blank" class="mt-auto inline-flex items-center justify-center gap-2 text-sm gradient-bg text-white font-semibold py-2 px-4 rounded-lg">Baixar Guia</a>
                    </div>
                    <div class="bg-gray-800 p-6 rounded-2xl shadow-md border border-blue-800 flex flex-col">
                        <h3 class="text-xl font-semibold mb-4 text-blue-400">✅ Check-list de Progresso</h3>
                        <ul class="space-y-3 text-left text-gray-300">{goals_html}</ul>
                    </div>
                </div>
            </section>
            
            <section id="resultados">
                <h2 class="text-3xl font-bold mb-6 border-l-4 border-blue-500 pl-4">5. Relatórios e Resultados</h2>
                <div class="grid md:grid-cols-1 lg:grid-cols-2 gap-8">
                    <div class="bg-gray-800 p-6 rounded-2xl shadow-lg border border-gray-700">
                        <h3 class="text-xl font-semibold mb-4 text-blue-400">📊 Relatório Mensal de Evolução</h3>
                        <div id="chart-container" class="w-full">
                            <div class="flex justify-center gap-2 mb-4 flex-wrap">
                                <button data-metric="fat" class="chart-filter-btn px-3 py-1 bg-gray-700 rounded-md text-sm">Gordura (%)</button>
                                <button data-metric="muscle" class="chart-filter-btn px-3 py-1 bg-gray-700 rounded-md text-sm">Músculo (kg)</button>
                                <button data-metric="water" class="chart-filter-btn px-3 py-1 bg-gray-700 rounded-md text-sm">Água (%)</button>
                                <button data-metric="metabolism" class="chart-filter-btn px-3 py-1 bg-gray-700 rounded-md text-sm">Metabolismo (kcal)</button>
                            </div>
                            <canvas id="evolutionChart"></canvas>
                        </div>
                    </div>
                    <div class="bg-gray-800 p-6 rounded-2xl shadow-lg flex flex-col justify-center items-center text-center border border-gray-700">
                        <h3 class="text-xl font-semibold mb-4 text-blue-400">🎯 Previsão de Resultados</h3>
                        <p class="text-gray-300 text-lg">{prediction_text}</p>
                    </div>
                </div>
            </section>
        </main>
        <footer class="text-center mt-16 py-6 border-t border-gray-700">
            <p class="text-gray-500">Este é o início da sua jornada para a máxima performance.</p>
            <p class="text-gray-400 font-semibold">Vamos juntos, {name_first}!</p>
            <div class="mt-4">
                <p class="font-bold text-gray-200">Caio Araújo</p>
                <p class="text-sm text-gray-500">Nutricionista | CRN 24103010</p>
            </div>
        </footer>
    </div>
    <script>
        document.addEventListener('DOMContentLoaded', () => {{
            const dataScript = document.getElementById('patient-data');
            if (!dataScript) return;

            const patientData = JSON.parse(dataScript.textContent);
            const evolutionData = patientData.evolution;

            if (!evolutionData || evolutionData.length === 0) {{
                document.getElementById('chart-container').innerHTML = '<p class="text-center text-gray-400">Nenhum dado de evolução mensal registrado.</p>';
                return;
            }}

            const labels = evolutionData.map(d => 'Mês ' + d.month);
            const metrics = {{
                fat: {{ label: 'Gordura (%)', data: evolutionData.map(d => parseFloat(d.fat) || 0) }},
                muscle: {{ label: 'Músculo (kg)', data: evolutionData.map(d => parseFloat(d.muscle) || 0) }},
                water: {{ label: 'Água (%)', data: evolutionData.map(d => parseFloat(d.water) || 0) }},
                metabolism: {{ label: 'Metabolismo (kcal)', data: evolutionData.map(d => parseFloat(d.metabolism) || 0) }}
            }};

            const ctx = document.getElementById('evolutionChart').getContext('2d');
            const evolutionChart = new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: labels,
                    datasets: [{{
                        label: 'Selecione um indicador',
                        data: [],
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.2)',
                        fill: true,
                        tension: 0.1
                    }}]
                }},
                options: {{
                    responsive: true,
                    scales: {{
                        y: {{ beginAtZero: true, ticks: {{ color: '#cbd5e1' }}, grid: {{ color: 'rgba(255, 255, 255, 0.1)' }} }},
                        x: {{ ticks: {{ color: '#cbd5e1' }}, grid: {{ color: 'rgba(255, 255, 255, 0.1)' }} }}
                    }},
                    plugins: {{ legend: {{ labels: {{ color: '#cbd5e1' }} }} }}
                }}
            }});

            const buttons = document.querySelectorAll('.chart-filter-btn');
            
            function updateChart(metricKey) {{
                const metric = metrics[metricKey];
                evolutionChart.data.datasets[0].label = metric.label;
                evolutionChart.data.datasets[0].data = metric.data;
                evolutionChart.update();
                
                buttons.forEach(btn => {{
                    btn.classList.toggle('active', btn.dataset.metric === metricKey);
                }});
            }}

            buttons.forEach(button => {{
                button.addEventListener('click', () => {{
                    updateChart(button.dataset.metric);
                }});
            }});

            if(buttons.length > 0) {{
                updateChart(buttons[0].dataset.metric);
            }}
        }});
    </script>
</body>
</html>
"""

# --- ROTAS DA APLICAÇÃO ---

@app.route('/')
@login_required
def index():
    if current_user.role == 'nutricionista':
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('view_plan'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user_from_db = load_user(username)
        
        if user_from_db and user_from_db.password == password:
            login_user(user_from_db)
            flash('Login bem-sucedido!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuário ou senha inválidos.', 'error')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
@nutritionist_required
def dashboard():
    try:
        users_df = pd.read_csv(USER_DB_PATH)
        # Filtra apenas pacientes que também são 'ativos'
        active_patients = users_df[(users_df['role'] == 'paciente') & (users_df['status'] == 'active')].to_dict('records')
        return render_template('dashboard.html', patients=active_patients)
    except FileNotFoundError:
        flash("Arquivo de pacientes não encontrado.", "error")
        return render_template('dashboard.html', patients=[])
    
@app.route('/create_patient', methods=['GET', 'POST'])
@login_required
@nutritionist_required
def create_patient():
    # Se o método for POST, significa que o formulário foi enviado
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Validação simples para não deixar campos em branco
        if not username or not password:
            flash('Nome de usuário e senha são obrigatórios.', 'error')
            return redirect(url_for('create_patient'))

        try:
            # Lê o CSV para verificar se o usuário já existe
            users_df = pd.read_csv(USER_DB_PATH)
            if username in users_df['username'].values:
                flash(f"O nome de usuário '{username}' já existe. Por favor, escolha outro.", 'error')
                return redirect(url_for('create_patient'))
        except FileNotFoundError:
            # Se o arquivo não existe, cria um DataFrame vazio
            users_df = pd.DataFrame(columns=['username', 'password', 'role'])

        # Cria um novo DataFrame para o novo paciente
        new_patient = pd.DataFrame({
            'username': [username],
            'password': [password],
            'role': ['paciente'],
            'status': ['active']
        })

        # Adiciona o novo paciente ao DataFrame existente
        updated_users_df = pd.concat([users_df, new_patient], ignore_index=True)
        
        # Salva o DataFrame atualizado de volta no arquivo CSV
        updated_users_df.to_csv(USER_DB_PATH, index=False)

        flash(f"Paciente '{username}' criado com sucesso!", 'success')
        return redirect(url_for('dashboard'))

    # Se o método for GET, apenas mostra a página de criação
    return render_template('create_patient.html')

@app.route('/archived')
@login_required
@nutritionist_required
def archived_patients():
    try:
        users_df = pd.read_csv(USER_DB_PATH)
        # Filtra apenas pacientes que são 'arquivados'
        archived = users_df[(users_df['role'] == 'paciente') & (users_df['status'] == 'archived')].to_dict('records')
        return render_template('archived.html', patients=archived)
    except FileNotFoundError:
        flash("Arquivo de pacientes não encontrado.", "error")
        return render_template('archived.html', patients=[])

def set_patient_status(username, status):
    """Função auxiliar para mudar o status de um paciente no CSV."""
    try:
        users_df = pd.read_csv(USER_DB_PATH)
        # Encontra o índice do paciente e atualiza o status
        users_df.loc[users_df['username'] == username, 'status'] = status
        users_df.to_csv(USER_DB_PATH, index=False)
        return True
    except FileNotFoundError:
        return False

@app.route('/archive/<username>')
@login_required
@nutritionist_required
def archive_patient(username):
    if set_patient_status(username, 'archived'):
        flash(f'Paciente {username} arquivado com sucesso.', 'success')
    else:
        flash('Erro ao arquivar o paciente.', 'error')
    return redirect(url_for('dashboard'))

@app.route('/restore/<username>')
@login_required
@nutritionist_required
def restore_patient(username):
    if set_patient_status(username, 'active'):
        flash(f'Paciente {username} restaurado com sucesso.', 'success')
    else:
        flash('Erro ao restaurar o paciente.', 'error')
    # Redireciona de volta para a lista de arquivados
    return redirect(url_for('archived_patients'))

@app.route('/view')
@login_required
def view_plan():
    if current_user.role == 'nutricionista':
        return redirect(url_for('dashboard'))
        
    patient_file = f"{current_user.id}.html"
    patient_file_path = os.path.join(PATIENT_DATA_FOLDER, patient_file)

    if os.path.exists(patient_file_path):
        return send_from_directory(PATIENT_DATA_FOLDER, patient_file)
    else:
        return """
        <body style='font-family: sans-serif; background-color: #111827; color: #e5e7eb; display: flex; align-items: center; justify-content: center; height: 100vh; text-align: center;'>
            <div>
                <h1>Aguardando Plano</h1>
                <p>Seu plano nutricional ainda não foi gerado pelo nutricionista.</p>
                <a href="/logout" style="color: #3b82f6; margin-top: 20px; display: inline-block;">Sair</a>
            </div>
        </body>
        """

@app.route('/edit/<username>')
@login_required
@nutritionist_required
def edit_plan(username):
    patient_data = {}
    patient_file = f"{username}.html"
    patient_file_path = os.path.join(PATIENT_DATA_FOLDER, patient_file)

    if os.path.exists(patient_file_path):
        try:
            with open(patient_file_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")
                data_script = soup.find("script", {"id": "patient-data"})
                if data_script:
                    patient_data = json.loads(data_script.string)
        except Exception as e:
            flash(f"Erro ao carregar dados existentes: {e}", "error")
    
    # ### INÍCIO DA CORREÇÃO ###
    # Garante que a estrutura de dados esteja completa antes de enviar para o template.
    
    # Cria um dicionário com os dados de evolução existentes, usando o mês como chave.
    existing_evo_data = {item['month']: item for item in patient_data.get('evolution', [])}
    
    # Cria uma nova lista de evolução que conterá todos os 12 meses.
    complete_evolution_list = []
    for month_num in range(1, 13):
        # Se os dados para o mês atual já existem, nós os usamos.
        if month_num in existing_evo_data:
            complete_evolution_list.append(existing_evo_data[month_num])
        # Se não existem, criamos um dicionário "fantasma" com valores em branco.
        else:
            complete_evolution_list.append({
                'month': month_num, 'fat': '', 'muscle': '', 'water': '', 'metabolism': ''
            })
            
    # Garante que a chave 'evolution' exista e a preenche com a lista completa.
    patient_data['evolution'] = complete_evolution_list
    
    # Garante que as outras chaves principais também existam para evitar erros.
    default_keys = {
        "name": username.replace('%20', ' '), "details": "", "consultation_date": datetime.now().strftime('%d/%m/%Y'),
        "bioimpedance": {}, "habits": {}, "signals": [], "plan": {}, "results": {},
        "goals": [{"text": "", "completed": False} for _ in range(3)]
    }
    for key, default_value in default_keys.items():
        patient_data.setdefault(key, default_value)
    # ### FIM DA CORREÇÃO ###

    return render_template('edit_plan.html', username=username, patient=patient_data)


@app.route('/save_plan/<username>', methods=['POST'])
@login_required
@nutritionist_required
def save_plan(username):
    data = {
        "name": request.form.get("name"), "details": request.form.get("details"), "consultation_date": request.form.get("consultation_date"),
        "bioimpedance": {"fat_percentage": request.form.get("fat_percentage"), "muscle_mass": request.form.get("muscle_mass"), "water_percentage": request.form.get("water_percentage"), "basal_metabolism": request.form.get("basal_metabolism"), "url": request.form.get("bioimpedance_url")},
        "habits": {"food_plan_text": request.form.get("food_plan_text"), "errors": request.form.get("errors"), "improvements": request.form.get("improvements"), "url": request.form.get("food_plan_url")},
        "signals": request.form.get("signals", "").strip().split('\n'),
        "plan": {"substitutions_example": request.form.get("substitutions_example"), "supplements": request.form.get("supplements", "").strip().split('\n'), "shopping_prioritize": request.form.get("shopping_prioritize"), "shopping_avoid": request.form.get("shopping_avoid")},
        "results": {"prediction_text": request.form.get("prediction_text")},
        "goals": [{"text": request.form.get(f"goal_text_{i}"), "completed": request.form.get(f"goal_completed_{i}") == 'on'} for i in range(3)],
        "evolution": []
    }

    for i in range(1, 13):
        fat = request.form.get(f'evo_fat_{i}')
        muscle = request.form.get(f'evo_muscle_{i}')
        water = request.form.get(f'evo_water_{i}')
        metabolism = request.form.get(f'evo_metabolism_{i}')
        # Adiciona à lista de evolução apenas se algum campo do mês foi preenchido.
        if fat or muscle or water or metabolism:
             data["evolution"].append({'month': i, 'fat': fat, 'muscle': muscle, 'water': water, 'metabolism': metabolism})

    bio_url = data.get("bioimpedance", {}).get("url")
    plan_url = data.get("habits", {}).get("url")
    bio_btn_html = f'<a href="{bio_url}" target="_blank" class="mt-auto inline-flex items-center justify-center gap-2 text-sm gradient-bg text-white font-semibold py-2 px-4 rounded-lg hover:opacity-90 transition-opacity">Baixar Análise Detalhada</a>' if bio_url else ""
    plan_btn_html = f'<a href="{plan_url}" target="_blank" class="mt-3 inline-flex items-center gap-2 text-sm gradient-bg text-white font-semibold py-2 px-4 rounded-lg hover:opacity-90 transition-opacity">Baixar Plano Alimentar</a>' if plan_url else ""
    goals_html = "".join([f'<li class="flex items-center {"text-green-400" if g["completed"] else ""}">{get_goal_icon(g["completed"])}<span>{g["text"]}</span></li>' for g in data["goals"] if g['text']])
    signals_html = "".join([f'<li>{s}</li>' for s in data["signals"] if s])
    supplements_html = "".join([f'<li>{s}</li>' for s in data.get("plan", {}).get("supplements", []) if s])

    format_args = {
        "json_data": json.dumps(data, indent=4, ensure_ascii=False), "name": data["name"], "details": data["details"], "consultation_date": data["consultation_date"],
        "fat_percentage": data.get("bioimpedance", {}).get("fat_percentage", "N/A"), "muscle_mass": data.get("bioimpedance", {}).get("muscle_mass", "N/A"),
        "water_percentage": data.get("bioimpedance", {}).get("water_percentage", "N/A"), "basal_metabolism": data.get("bioimpedance", {}).get("basal_metabolism", "N/A"),
        "bio_download_button_html": bio_btn_html, "food_plan_text": data.get("habits", {}).get("food_plan_text", ""),
        "plan_download_button_html": plan_btn_html, "errors": data.get("habits", {}).get("errors", ""), "improvements": data.get("habits", {}).get("improvements", ""),
        "signals_html": signals_html, "substitutions_example": data.get("plan", {}).get("substitutions_example", ""), "supplements_html": supplements_html,
        "shopping_prioritize": data.get("plan", {}).get("shopping_prioritize", ""), "shopping_avoid": data.get("plan", {}).get("shopping_avoid", ""),
        "prediction_text": data.get("results", {}).get("prediction_text", ""), "goals_html": goals_html, "name_first": data["name"].split(' ')[0] if data["name"] else ""
    }

    final_html = HTML_TEMPLATE_CLIENTE.format(**format_args)
    
    filepath = os.path.join(PATIENT_DATA_FOLDER, f"{username}.html")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(final_html)

    flash(f"Plano do paciente '{username}' salvo com sucesso!", "success")
    return redirect(url_for('dashboard'))

def get_goal_icon(completed):
    if completed:
        return '<svg class="h-5 w-5 mr-3" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" /></svg>'
    return '<svg class="animate-spin h-5 w-5 mr-3 text-blue-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>'

# --- EXECUTAR A APLICAÇÃO ---
if __name__ == "__main__":
    app.run(debug=True)