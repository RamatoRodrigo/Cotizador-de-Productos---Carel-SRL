# services/processor.py
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def calculate_unit_price(df):
    """Calcula precio unitario con validaciones"""
    df = df.copy()
    
    # Validar que quantity no sea 0
    df = df[df['quantity'] > 0]
    
    df['unit_price'] = df['price'] / df['quantity']
    
    return df

def process_data(dfs, config):
    """
    Procesa datos de múltiples proveedores.
    
    Retorna DataFrame con comparativa de precios y sugerencias
    """
    if not dfs or all(df.empty for df in dfs):
        logger.error("No hay datos para procesar")
        return pd.DataFrame()
    
    processed = []
    
    for df in dfs:
        if df.empty:
            continue
        df = calculate_unit_price(df)
        processed.append(df)
    
    if not processed:
        return pd.DataFrame()
    
    merged = pd.concat(processed, ignore_index=True)
    
    results = []
    
    for desc, group in merged.groupby('description'):
        prices_data = group[['provider', 'unit_price', 'price', 'quantity']].values
        prices_sorted = sorted(prices_data, key=lambda x: x[1])
        
        best = prices_sorted[0]
        second = prices_sorted[1] if len(prices_sorted) > 1 else best
        
        results.append({
            'description': desc,
            'best_provider': best[0],
            'best_price': best[1],
            'best_total': best[2],
            'second_provider': second[0],
            'second_price': second[1],
            'suggested_28': round(second[1] * (1 + config['markup_1']), 2),
            'suggested_36': round(second[1] * (1 + config['markup_2']), 2),
            'providers_count': len(prices_sorted)
        })
    
    return pd.DataFrame(results)