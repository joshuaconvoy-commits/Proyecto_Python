import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import os

# Importar plotly con manejo de errores
try:
    import plotly.express as px
    import plotly.graph_objects as go
except ImportError:
    st.error("Error: No se pudo importar plotly. Instalando dependencias...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "plotly"])
    import plotly.express as px
    import plotly.graph_objects as go

pd.options.mode.chained_assignment = None  # default='warn'

# Configuración de la página
st.set_page_config(
    page_title="Dashboard de Casos",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Aplicar estilo personalizado
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric .metric-value {
        font-size: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Función para cargar datos
@st.cache_data(ttl=3600)  # Caché por 1 hora
def load_data():
    """
    Carga los datos desde la carpeta data/.
    Intenta primero con CSV, luego con JSON si es necesario.
    """
    data_dir = Path("data")
    
    try:
        # Buscar archivos CSV primero
        csv_files = list(data_dir.glob("*.csv"))
        if csv_files:
            # Leer el CSV con manejo de codificación
            df = pd.read_csv(csv_files[0], sep=';', encoding='utf-8')
            
            # Limpiar nombres de columnas
            df.columns = df.columns.str.strip()
            
            # Asegurar que las columnas numéricas sean numéricas
            if 'Duración' in df.columns:
                df['Duración'] = pd.to_numeric(df['Duración'], errors='coerce')
            
            # Convertir la columna de fecha y ordenar
            if 'Fecha Límite' in df.columns:
                df['Fecha Límite'] = pd.to_datetime(df['Fecha Límite'], errors='coerce')
                df = df.sort_values('Fecha Límite')
            
            # Rellenar valores NaN
            for col in df.select_dtypes(include=['object']):
                df[col] = df[col].fillna('No especificado')
            
            # Limpiar espacios en blanco en columnas de texto
            for col in df.select_dtypes(include=['object']):
                df[col] = df[col].str.strip()
            
            return df
    except Exception as e:
        st.error(f"Error al cargar el archivo: {str(e)}")
        return pd.DataFrame()
    
    # Si no hay CSV, buscar JSON
    json_files = list(data_dir.glob("*.json"))
    if json_files:
        return pd.read_json(json_files[0])
    
    # Si no hay datos, usar datos de ejemplo
    return pd.DataFrame({
        'fecha': pd.date_range('2023-01-01', '2023-12-31', freq='D'),
        'ventas': np.random.randint(100, 1000, 365),
        'categoria': np.random.choice(['A', 'B', 'C'], 365),
        'region': np.random.choice(['Norte', 'Sur', 'Este', 'Oeste'], 365),
    })

def get_kpi_metrics(df):
    """
    Calcula métricas clave (KPIs) del DataFrame
    """
    kpis = []
    
    # Total de casos
    total_casos = len(df)
    kpis.append({
        'title': 'Total de Casos',
        'value': total_casos,
        'delta': 'casos registrados',
        'help': 'Número total de casos en el sistema'
    })
    
    # Métrica de Duración
    if 'Duración' in df.columns:
        duracion_media = df['Duración'].mean()
        duracion_std = df['Duración'].std()
        kpis.append({
            'title': 'Duración Promedio',
            'value': f"{duracion_media:.1f}",
            'delta': f"±{duracion_std:.1f} días",
            'help': 'Promedio y desviación estándar de la duración de los casos'
        })
    
    # Próximos vencimientos (próximos 30 días)
    if 'Fecha Límite' in df.columns:
        today = pd.Timestamp.now()
        proximos = df[df['Fecha Límite'].between(today, today + pd.Timedelta(days=30))]
        kpis.append({
            'title': 'Próximos Vencimientos',
            'value': len(proximos),
            'delta': 'en los próximos 30 días',
            'help': 'Casos que vencen en los próximos 30 días'
        })
    
    # Top actuaciones
    if 'Actuación' in df.columns:
        top_actuacion = df['Actuación'].value_counts().iloc[0]
        top_actuacion_nombre = df['Actuación'].value_counts().index[0]
        kpis.append({
            'title': 'Actuación más Común',
            'value': str(top_actuacion_nombre)[:20] + '...' if len(str(top_actuacion_nombre)) > 20 else str(top_actuacion_nombre),
            'delta': f"{top_actuacion} casos",
            'help': 'Tipo de actuación más frecuente'
        })
    
    return kpis

# Cargar datos
try:
    df = load_data()
    
    # Título principal
    st.title("📊 Dashboard Interactivo")
    
    # Sección 1: Línea de Tiempo y Gráfico de Líneas
    st.subheader("Evolución Temporal")
    
    # Usar la columna Fecha Límite para la línea temporal
    date_col = 'Fecha Límite' if 'Fecha Límite' in df.columns else None
    
    # Asegurarse de que la fecha esté en formato datetime
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col])
    
    # Gráfico de línea temporal
    if date_col and 'Duración' in df.columns:
        # Calcular la media
        media_duracion = df['Duración'].mean()
        
        # Ordenar el DataFrame por fecha
        df_sorted = df.sort_values(by=date_col)
        
        # Crear el gráfico base con la línea de duración
        fig_timeline = px.line(
            df_sorted,
            x=date_col,
            y='Duración',
            title='Evolución de la Duración de Casos'
        )
        
        # Agregar la línea de la media
        fig_timeline.add_hline(
            y=media_duracion,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Media: {media_duracion:.2f}",
            annotation_position="top right"
        )
        
        # Actualizar el diseño
        fig_timeline.update_layout(
            showlegend=True,
            hovermode='x unified'
        )
        
        # Actualizar las trazas para mostrar leyendas
        fig_timeline.data[0].name = 'Duración'
        
        st.plotly_chart(fig_timeline, use_container_width=True)
    
    # Sección 2: Tarjetas de KPIs
    st.subheader("📊 Métricas Clave")
    kpi_metrics = get_kpi_metrics(df)
    
    # Crear filas de métricas con 4 tarjetas por fila
    cols = st.columns(4)
    for idx, kpi in enumerate(kpi_metrics):
        with cols[idx % 4]:
            st.metric(
                label=kpi['title'],
                value=kpi['value'],
                delta=kpi['delta'],
                help=kpi.get('help', '')
            )
    
    # Sección 3: Gráficos Detallados
    st.subheader("Análisis Detallado")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de barras
        categorical_cols = df.select_dtypes(include=['object']).columns
        if len(categorical_cols) > 0:
            cat_col = categorical_cols[0]
            st.write(f"### Conteo de {cat_col}")
            # Asegurar que no hay valores nulos antes de hacer value_counts
            counts = df[cat_col].fillna('No especificado').value_counts()
            st.write(pd.DataFrame({
                'Categoría': counts.index,
                'Cantidad': counts.values
            }))
        
        # Gráfico de torta con top 5
        if len(categorical_cols) > 1:
            cat_col2 = categorical_cols[1]
            # Obtener el conteo de valores
            value_counts = df[cat_col2].value_counts()
            
            # Separar top 5 y agrupar el resto
            top_5 = value_counts.head(5)
            others = pd.Series({'Otros': value_counts[5:].sum()}) if len(value_counts) > 5 else pd.Series({})
            
            # Combinar top 5 y otros
            final_counts = pd.concat([top_5, others])
            
            # Crear DataFrame para el gráfico
            pie_data = pd.DataFrame({
                'Categoría': final_counts.index,
                'Cantidad': final_counts.values
            })
            
            fig_pie = px.pie(
                pie_data,
                values='Cantidad',
                names='Categoría',
                title=f'Top 5 - {cat_col2}',
            )
            
            # Actualizar el diseño
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Segundo gráfico de barras
        if len(categorical_cols) > 2:
            cat_col3 = categorical_cols[2]
            st.write(f"### Conteo de {cat_col3}")
            st.write(df[cat_col3].value_counts())
        
        # Segundo gráfico de torta con top 5
        if len(categorical_cols) > 3:
            cat_col4 = categorical_cols[3]
            # Obtener el conteo de valores
            value_counts = df[cat_col4].value_counts()
            
            # Separar top 5 y agrupar el resto
            top_5 = value_counts.head(5)
            others = pd.Series({'Otros': value_counts[5:].sum()}) if len(value_counts) > 5 else pd.Series({})
            
            # Combinar top 5 y otros
            final_counts = pd.concat([top_5, others])
            
            # Crear DataFrame para el gráfico
            pie_data = pd.DataFrame({
                'Categoría': final_counts.index,
                'Cantidad': final_counts.values
            })
            
            fig_pie2 = px.pie(
                pie_data,
                values='Cantidad',
                names='Categoría',
                title=f'Top 5 - {cat_col4}',
            )
            
            # Actualizar el diseño
            fig_pie2.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie2.update_layout(
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig_pie2, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar o procesar los datos: {str(e)}")
    st.info("Por favor, asegúrese de tener archivos de datos (.csv o .json) en la carpeta 'data/'")

