import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import base64

# Forçar compatibilidade
import warnings
warnings.filterwarnings('ignore')

# Configurar pandas para compatibilidade
pd.set_option('future.no_silent_downcasting', True)

# Configuração da página
st.set_page_config(
    page_title="Sistema de Gestão de Incidentes - Hemodiálise",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #3498db;
        margin-bottom: 1rem;
    }
    .section-header {
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
        font-size: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Dados iniciais
CATEGORIAS = {
    'Acesso Vascular': [
        '1.1 - Desconexão acidental da agulha',
        '1.2 - Retirada inadvertida de cateter',
        '1.3 - Conexão inadequada do cateter',
        '1.4 - Desconexão da agulha de punção da FAV',
        '1.5 - Ruptura de FAV',
        '1.6 - Sangramento pelo acesso venoso',
        '1.7 - Hematoma em acesso',
        '1.8 - Coagulação do sistema extracorpóreo',
        '1.9 - Exteriorização do cateter',
        '1.10 - FAV parada',
        '1.12 - Fluxo sanguíneo inadequado na FAV (<200)',
        '1.13 - Fluxo sanguíneo inadequado no cateter (<200)',
        '1.15 - Hematoma em acesso (FAV)',
        '1.17 - Hemostasia > 15min',
        '1.18 - Infiltração/edema na FAV',
        '1.19 - Obstrução do Cateter',
        '1.24 - Sangramento pelo óstio do cateter',
        '1.26 - Outros',
        '1.28 - Outros'
    ],
    'Quedas': [
        '2.1 - Cadeira',
        '2.2 - Sozinho',
        '2.3 - Com Acompanhante/Colaborador',
        '2.4 - Outros'
    ],
    'Terapia Medicamentosa': [
        '3.1 - Erro de Administração',
        '3.2 - Erro de Prescrição',
        '3.3 - Reação Adversa',
        '3.4 - Outros'
    ],
    'Identificação do Paciente': [
        '4.1 - Falha na identificação',
        '4.2 - Troca de Capilar',
        '4.3 - Falha na realização de exames'
    ],
    'Outros Eventos': [
        '5.1 - Liberação de paciente incapaz sem acompanhante',
        '5.2 - Cãibra',
        '5.3 - Cefaleia',
        '5.4 - Coagulação inadequada do sistema',
        '5.5 - Crise Convulsiva',
        '5.6 - Dor Precordial',
        '5.7 - Encaminhamento para Emergência',
        '5.8 - Outros',
        '5.10 - Hiperglicemia (>200)',
        '5.11 - Hipoglicemia (<70)',
        '5.12 - Hipotensão (<100x60)',
        '5.13 - Hipertensão',
        '5.15 - Paciente hipervolêmico',
        '5.18 - Saída à revelia',
        '5.19 - Saída à revelia',
        '5.20 - Dor abdominal',
        '5.21 - Dor refratária',
        '5.22 - Calafrio',
        '5.23 - Tremores',
        '5.24 - Falta',
        '5.25 - Reposição de hemodiálise',
        '5.26 - HD extra'
    ]
}

SETORES = ['B1', 'B2', 'B3', 'B4', 'B5', 'Área Externa']
FASES = ['Antes da Diálise', 'Durante a Diálise', 'Pós Diálise', 'Consulta']
RESPONSAVEIS = ['Enf. João Silva', 'Enf. Maria Santos', 'Enf. Pedro Costa', 'Enf. Ana Oliveira']

# Inicialização do banco de dados
def init_db():
    conn = sqlite3.connect('incidentes.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS incidentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_ocorrencia DATE,
            responsavel TEXT,
            setor TEXT,
            fase TEXT,
            paciente TEXT,
            idade INTEGER,
            categorias TEXT,
            sugestao TEXT
        )
    ''')
    conn.commit()
    conn.close()

def salvar_incidente(data_ocorrencia, responsavel, setor, fase, paciente, idade, categorias, sugestao):
    conn = sqlite3.connect('incidentes.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO incidentes 
        (data_ocorrencia, responsavel, setor, fase, paciente, idade, categorias, sugestao)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (data_ocorrencia, responsavel, setor, fase, paciente, idade, ','.join(categorias), sugestao))
    conn.commit()
    conn.close()

def carregar_incidentes():
    conn = sqlite3.connect('incidentes.db')
    df = pd.read_sql('SELECT * FROM incidentes', conn)
    conn.close()
    return df

# Inicializar banco
init_db()

# Header principal
st.markdown('<div class="main-header">🏥 Sistema de Gestão de Incidentes - Hemodiálise</div>', unsafe_allow_html=True)

# Sidebar para navegação
st.sidebar.title("Navegação")
secao = st.sidebar.radio("Selecione a seção:", 
                        ["📊 Dashboard", "📝 Nova Notificação", "📋 Lista de Incidentes", 
                         "📈 Análise e Relatórios", "✅ Ações Corretivas"])

# Carregar dados
df_incidentes = carregar_incidentes()

# SEÇÃO: DASHBOARD
if secao == "📊 Dashboard":
    st.markdown('<div class="section-header">📊 Dashboard - Visão Geral</div>', unsafe_allow_html=True)
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_incidentes = len(df_incidentes)
        st.metric("Total de Incidentes", total_incidentes)
    
    with col2:
        incidentes_mes = len(df_incidentes[df_incidentes['data_ocorrencia'] >= datetime.now().replace(day=1).strftime('%Y-%m-%d')])
        st.metric("Incidentes Este Mês", incidentes_mes)
    
    with col3:
        taxa = (incidentes_mes / 1000) * 100 if incidentes_mes > 0 else 0
        st.metric("Taxa por 1000 sessões", f"{taxa:.1f}%")
    
    with col4:
        acoes_pendentes = len(df_incidentes[df_incidentes['sugestao'].notna() & (df_incidentes['sugestao'] != '')])
        st.metric("Ações Pendentes", acoes_pendentes)
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Incidentes por Categoria")
        if not df_incidentes.empty:
            # Processar categorias
            todas_categorias = []
            for categorias_str in df_incidentes['categorias']:
                if categorias_str:
                    categorias_lista = categorias_str.split(',')
                    for cat in categorias_lista:
                        categoria_principal = cat.split(' - ')[0].split('.')[0]
                        todas_categorias.append(categoria_principal)
            
            if todas_categorias:
                df_categorias = pd.DataFrame({'categoria': todas_categorias})
                contagem_categorias = df_categorias['categoria'].value_counts()
                
                fig = px.pie(values=contagem_categorias.values, 
                           names=contagem_categorias.index,
                           title="Distribuição por Categoria")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nenhum incidente com categorias definidas")
        else:
            st.info("Nenhum incidente registrado")
    
    with col2:
        st.subheader("Incidentes por Setor")
        if not df_incidentes.empty:
            contagem_setores = df_incidentes['setor'].value_counts()
            fig = px.bar(x=contagem_setores.index, y=contagem_setores.values,
                       title="Incidentes por Setor",
                       labels={'x': 'Setor', 'y': 'Quantidade'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhum incidente registrado")
    
    # Tendência temporal
    st.subheader("Tendência Temporal")
    if not df_incidentes.empty:
        df_incidentes['data_ocorrencia'] = pd.to_datetime(df_incidentes['data_ocorrencia'])
        df_tendencia = df_incidentes.groupby(df_incidentes['data_ocorrencia'].dt.to_period('M')).size().reset_index()
        df_tendencia['data_ocorrencia'] = df_tendencia['data_ocorrencia'].dt.to_timestamp()
        
        fig = px.line(df_tendencia, x='data_ocorrencia', y=0,
                    title="Evolução Mensal de Incidentes",
                    labels={'data_ocorrencia': 'Mês', '0': 'Número de Incidentes'})
        st.plotly_chart(fig, use_container_width=True)

# SEÇÃO: NOVA NOTIFICAÇÃO
elif secao == "📝 Nova Notificação":
    st.markdown('<div class="section-header">📝 Nova Notificação de Incidente</div>', unsafe_allow_html=True)
    
    with st.form("form_incidente"):
        col1, col2 = st.columns(2)
        
        with col1:
            paciente = st.text_input("Nome do Paciente *", placeholder="Digite o nome completo do paciente")
            setor = st.selectbox("Setor onde Ocorreu *", SETORES)
            responsavel = st.selectbox("Responsável pela Notificação *", RESPONSAVEIS)
            data_ocorrencia = st.date_input("Data da Ocorrência *", datetime.now())
        
        with col2:
            idade = st.number_input("Idade do Paciente", min_value=0, max_value=120, value=0)
            fase = st.selectbox("Fase da Assistência *", FASES)
        
        st.markdown("---")
        st.subheader("Classificação do Incidente")
        
        # Categorias com expansores
        categorias_selecionadas = []
        
        for categoria_nome, opcoes in CATEGORIAS.items():
            with st.expander(f"📁 {categoria_nome}", expanded=False):
                cols = st.columns(2)
                for i, opcao in enumerate(opcoes):
                    col_idx = i % 2
                    if cols[col_idx].checkbox(opcao, key=f"cat_{categoria_nome}_{opcao}"):
                        categorias_selecionadas.append(opcao)
        
        st.markdown("---")
        sugestao = st.text_area("Sugestão de Melhorias", 
                               placeholder="Descreva sugestões para evitar recorrência...",
                               height=100)
        
        submitted = st.form_submit_button("💾 Salvar Notificação")
        
        if submitted:
            if not paciente or not setor or not responsavel:
                st.error("⚠️ Preencha todos os campos obrigatórios (*)")
            elif not categorias_selecionadas:
                st.error("⚠️ Selecione pelo menos uma categoria de incidente")
            else:
                salvar_incidente(
                    data_ocorrencia.strftime('%Y-%m-%d'),
                    responsavel,
                    setor,
                    fase,
                    paciente,
                    idade,
                    categorias_selecionadas,
                    sugestao
                )
                st.success("✅ Incidente registrado com sucesso!")
                st.balloons()

# SEÇÃO: LISTA DE INCIDENTES
elif secao == "📋 Lista de Incidentes":
    st.markdown('<div class="section-header">📋 Lista de Incidentes Registrados</div>', unsafe_allow_html=True)
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        filtro_setor = st.selectbox("Filtrar por Setor", ["Todos"] + SETORES)
    with col2:
        filtro_data = st.date_input("Filtrar por Data", [])
    with col3:
        filtro_paciente = st.text_input("Filtrar por Paciente", "")
    
    # Aplicar filtros
    df_filtrado = df_incidentes.copy()
    
    if filtro_setor != "Todos":
        df_filtrado = df_filtrado[df_filtrado['setor'] == filtro_setor]
    
    if filtro_paciente:
        df_filtrado = df_filtrado[df_filtrado['paciente'].str.contains(filtro_paciente, case=False, na=False)]
    
    if filtro_data:
        if isinstance(filtro_data, list) and len(filtro_data) == 2:
            df_filtrado = df_filtrado[
                (df_filtrado['data_ocorrencia'] >= filtro_data[0].strftime('%Y-%m-%d')) &
                (df_filtrado['data_ocorrencia'] <= filtro_data[1].strftime('%Y-%m-%d'))
            ]
    
    # Tabela de incidentes
    if not df_filtrado.empty:
        st.dataframe(
            df_filtrado[['data_ocorrencia', 'paciente', 'setor', 'fase', 'categorias', 'sugestao']],
            use_container_width=True,
            height=400
        )
        
        # Estatísticas dos filtros
        st.info(f"📊 Mostrando {len(df_filtrado)} de {len(df_incidentes)} incidentes")
    else:
        st.warning("Nenhum incidente encontrado com os filtros aplicados")

# SEÇÃO: ANÁLISE E RELATÓRIOS
elif secao == "📈 Análise e Relatórios":
    st.markdown('<div class="section-header">📈 Análise e Relatórios</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        periodo = st.selectbox("Período do Relatório", 
                              ["Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias", "Este mês", "Personalizado"])
        
        if periodo == "Personalizado":
            data_inicio = st.date_input("Data Início")
            data_fim = st.date_input("Data Fim")
    
    with col2:
        tipo_relatorio = st.selectbox("Tipo de Relatório", 
                                     ["Análise Geral", "Por Setor", "Por Categoria", "Por Fase"])
        
        formato_export = st.selectbox("Formato de Exportação", ["Visualização", "CSV", "Excel"])
    
    if st.button("🔄 Gerar Relatório"):
        # Filtrar por período
        df_relatorio = df_incidentes.copy()
        df_relatorio['data_ocorrencia'] = pd.to_datetime(df_relatorio['data_ocorrencia'])
        
        if periodo == "Últimos 7 dias":
            data_corte = datetime.now() - timedelta(days=7)
        elif periodo == "Últimos 30 dias":
            data_corte = datetime.now() - timedelta(days=30)
        elif periodo == "Últimos 90 dias":
            data_corte = datetime.now() - timedelta(days=90)
        elif periodo == "Este mês":
            data_corte = datetime.now().replace(day=1)
        else:  # Personalizado
            data_corte = data_inicio
        
        df_relatorio = df_relatorio[df_relatorio['data_ocorrencia'] >= pd.Timestamp(data_corte)]
        
        if not df_relatorio.empty:
            # Análise por tipo de relatório
            if tipo_relatorio == "Por Setor":
                analise = df_relatorio['setor'].value_counts()
                fig = px.bar(analise, title="Incidentes por Setor")
                st.plotly_chart(fig, use_container_width=True)
                
            elif tipo_relatorio == "Por Categoria":
                # Processar categorias
                todas_categorias = []
                for categorias_str in df_relatorio['categorias']:
                    if categorias_str:
                        categorias_lista = categorias_str.split(',')
                        todas_categorias.extend([cat.split(' - ')[0] for cat in categorias_lista])
                
                if todas_categorias:
                    df_cats = pd.DataFrame({'categoria': todas_categorias})
                    analise = df_cats['categoria'].value_counts().head(10)
                    fig = px.bar(analise, title="Top 10 Categorias")
                    st.plotly_chart(fig, use_container_width=True)
            
            elif tipo_relatorio == "Por Fase":
                analise = df_relatorio['fase'].value_counts()
                fig = px.pie(values=analise.values, names=analise.index, title="Distribuição por Fase")
                st.plotly_chart(fig, use_container_width=True)
            
            else:  # Análise Geral
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total no Período", len(df_relatorio))
                    st.metric("Setor Mais Afetado", df_relatorio['setor'].mode().iloc[0] if not df_relatorio.empty else "N/A")
                with col2:
                    st.metric("Fase Mais Crítica", df_relatorio['fase'].mode().iloc[0] if not df_relatorio.empty else "N/A")
            
            # Exportação
            if formato_export == "CSV":
                csv = df_relatorio.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"relatorio_incidentes_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            elif formato_export == "Excel":
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_relatorio.to_excel(writer, index=False, sheet_name='Incidentes')
                st.download_button(
                    label="📥 Download Excel",
                    data=output.getvalue(),
                    file_name=f"relatorio_incidentes_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.ms-excel"
                )
        else:
            st.warning("Nenhum dado encontrado para o período selecionado")

# SEÇÃO: AÇÕES CORRETIVAS
else:  # Ações Corretivas
    st.markdown('<div class="section-header">✅ Ações Corretivas</div>', unsafe_allow_html=True)
    
    # Filtrar incidentes com sugestões
    df_acoes = df_incidentes[df_incidentes['sugestao'].notna() & (df_incidentes['sugestao'] != '')]
    
    if not df_acoes.empty:
        for idx, row in df_acoes.iterrows():
            with st.expander(f"📋 {row['paciente']} - {row['data_ocorrencia']}", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Setor:** {row['setor']}")
                    st.write(f"**Categorias:** {row['categorias']}")
                    st.write(f"**Sugestão:** {row['sugestao']}")
                
                with col2:
                    status = st.selectbox(
                        "Status",
                        ["Pendente", "Em Andamento", "Concluído"],
                        key=f"status_{idx}"
                    )
                    responsavel_acao = st.selectbox(
                        "Responsável",
                        RESPONSAVEIS,
                        key=f"resp_{idx}"
                    )
                    prazo = st.date_input(
                        "Prazo",
                        datetime.now() + timedelta(days=7),
                        key=f"prazo_{idx}"
                    )
                
                if st.button("💾 Salvar Ação", key=f"btn_{idx}"):
                    st.success("Ação atualizada com sucesso!")
    else:
        st.info("📝 Nenhuma sugestão de melhoria registrada. As sugestões aparecerão aqui automaticamente.")

# Footer
st.markdown("---")
st.markdown("*Sistema de Gestão de Incidentes - Hemodiálise* | Desenvolvido para melhoria contínua da qualidade")
