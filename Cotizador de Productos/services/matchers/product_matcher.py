import pandas as pd
import logging
from typing import Tuple, Dict, Optional
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class ProductMatcher:
    """
    Clase para hacer matching entre productos de Carel y proveedores.
    
    Usa filtros progresivos (tipo, diámetro, paso, largo, grado, sistema)
    y calcula un score de similitud.
    """
    
    def __init__(self, threshold: float = 0.7):
        """
        Args:
            threshold: Score mínimo para considerar un match (0.0 a 1.0)
        """
        self.threshold = threshold
    
    def match_single(self, carel_row: Dict, provider_df: pd.DataFrame) -> Tuple[Optional[Dict], float, str]:
        """
        Busca el mejor match para un producto de Carel en los datos del proveedor.
        
        Args:
            carel_row: Fila del DataFrame de Carel
            provider_df: DataFrame del proveedor
            
        Returns:
            (mejor_match, score, tipo_match)
            - mejor_match: Dict con datos del proveedor que matcheó
            - score: Score de similitud (0.0 a 1.0)
            - tipo_match: 'exact', 'partial' o 'no_match'
        """
        
        candidates = provider_df.copy()
        
        # Filtro 1: Mismo tipo (exacto)
        if pd.notna(carel_row.get('tipo')):
            candidates = candidates[
                candidates['tipo'].str.lower() == str(carel_row['tipo']).lower()
            ]
            
            if candidates.empty:
                return None, 0.0, 'no_match'
        
        # Filtro 2: Mismo diámetro (exacto)
        if pd.notna(carel_row.get('diametro')):
            candidates = candidates[
                candidates['diametro'].astype(str) == str(carel_row['diametro'])
            ]
            
            if candidates.empty:
                return None, 0.0, 'no_match'
        
        # Filtro 3: Mismo paso (si existe en carel)
        if pd.notna(carel_row.get('paso')) and str(carel_row['paso']).lower() != 'none':
            paso_carel = str(carel_row['paso']).replace(',', '.')
            
            # Filtro exacto
            candidates_paso = candidates[
                candidates['paso'].astype(str).str.replace(',', '.') == paso_carel
            ]
            
            if not candidates_paso.empty:
                candidates = candidates_paso
        
        # Filtro 4: Mismo sistema (si existe)
        if pd.notna(carel_row.get('sistema')):
            candidates = candidates[
                candidates['sistema'].str.lower() == str(carel_row['sistema']).lower()
            ]
            
            if candidates.empty:
                return None, 0.0, 'no_match'
        
        if candidates.empty:
            return None, 0.0, 'no_match'
        
        # Filtro 5: Largo (fuzzy - permite variación)
        if pd.notna(carel_row.get('largo')) and str(carel_row['largo']).lower() != 'none':
            try:
                largo_carel = float(str(carel_row['largo']).replace(',', '.'))
                
                # Buscar largos cercanos (±2mm de tolerancia)
                candidates_largo = candidates.copy()
                candidates_largo['largo_float'] = pd.to_numeric(
                    candidates_largo['largo'].astype(str).str.replace(',', '.'),
                    errors='coerce'
                )
                
                candidates_largo = candidates_largo[
                    (candidates_largo['largo_float'] >= largo_carel - 2) &
                    (candidates_largo['largo_float'] <= largo_carel + 2)
                ]
                
                if not candidates_largo.empty:
                    candidates = candidates_largo
                    
            except (ValueError, AttributeError):
                pass
        
        # Filtro 6: Grado (si existe)
        if pd.notna(carel_row.get('grado')) and str(carel_row['grado']).lower() != 'none':
            candidates_grado = candidates[
                candidates['grado'].astype(str) == str(carel_row['grado'])
            ]
            
            if not candidates_grado.empty:
                candidates = candidates_grado
        
        if candidates.empty:
            return None, 0.0, 'no_match'
        
        # Calcular scores
        candidates = candidates.copy()
        candidates['_score'] = candidates.apply(
            lambda row: self._calculate_score(carel_row, row),
            axis=1
        )
        
        # Mejor match
        best_idx = candidates['_score'].idxmax()
        best_match = candidates.loc[best_idx]
        score = best_match['_score']
        
        # Determinar tipo de match
        if score >= 0.95:
            match_type = 'exact'
        elif score >= self.threshold:
            match_type = 'partial'
        else:
            match_type = 'no_match'
        
        return best_match.to_dict(), score, match_type
    
    def _calculate_score(self, carel_row: Dict, provider_row: pd.Series) -> float:
        """
        Calcula un score de similitud basado en coincidencias de campos.
        
        Returns:
            Score de 0.0 a 1.0
        """
        score = 0.0
        total_weight = 0.0
        
        # Tipo (peso 0.25)
        if pd.notna(carel_row.get('tipo')) and pd.notna(provider_row.get('tipo')):
            tipo_match = str(carel_row['tipo']).lower() == str(provider_row['tipo']).lower()
            score += 0.25 if tipo_match else 0.0
            total_weight += 0.25
        
        # Diámetro (peso 0.25)
        if pd.notna(carel_row.get('diametro')) and pd.notna(provider_row.get('diametro')):
            dia_match = str(carel_row['diametro']) == str(provider_row['diametro'])
            score += 0.25 if dia_match else 0.0
            total_weight += 0.25
        
        # Paso (peso 0.20)
        if pd.notna(carel_row.get('paso')) and pd.notna(provider_row.get('paso')):
            paso_carel = str(carel_row['paso']).replace(',', '.')
            paso_prov = str(provider_row['paso']).replace(',', '.')
            paso_match = paso_carel == paso_prov
            score += 0.20 if paso_match else 0.0
            total_weight += 0.20
        
        # Largo (peso 0.15)
        if pd.notna(carel_row.get('largo')) and pd.notna(provider_row.get('largo')):
            try:
                largo_carel = float(str(carel_row['largo']).replace(',', '.'))
                largo_prov = float(str(provider_row['largo']).replace(',', '.'))
                
                # Cercano dentro de ±2mm
                if abs(largo_carel - largo_prov) <= 2:
                    score += 0.15
                else:
                    score += max(0, 0.15 * (1 - abs(largo_carel - largo_prov) / 10))
                    
                total_weight += 0.15
            except (ValueError, AttributeError):
                pass
        
        # Grado (peso 0.15)
        if pd.notna(carel_row.get('grado')) and pd.notna(provider_row.get('grado')):
            grado_match = str(carel_row['grado']) == str(provider_row['grado'])
            score += 0.15 if grado_match else 0.0
            total_weight += 0.15
        
        if total_weight == 0:
            return 0.0
        
        return score / total_weight
    
    def match_all(self, carel_df: pd.DataFrame, provider_df: pd.DataFrame) -> pd.DataFrame:
        """
        Hace matching de todos los productos de Carel contra un proveedor.
        
        Returns:
            DataFrame con resultados de matching
        """
        results = []
        
        logger.info(f"Procesando {len(carel_df)} productos de Carel...")
        
        for idx, carel_row in carel_df.iterrows():
            match, score, match_type = self.match_single(carel_row, provider_df)
            
            result = {
                'carel_codigo': carel_row.get('codigo'),
                'carel_tipo': carel_row.get('tipo'),
                'carel_diametro': carel_row.get('diametro'),
                'carel_paso': carel_row.get('paso'),
                'carel_largo': carel_row.get('largo'),
                'carel_grado': carel_row.get('grado'),
                'carel_sistema': carel_row.get('sistema'),
                'carel_descripcion': carel_row.get('descripcion'),
                'match_codigo': match.get('codigo') if match else None,
                'match_tipo': match.get('tipo') if match else None,
                'match_diametro': match.get('diametro') if match else None,
                'match_paso': match.get('paso') if match else None,
                'match_largo': match.get('largo') if match else None,
                'match_grado': match.get('grado') if match else None,
                'match_sistema': match.get('sistema') if match else None,
                'match_precio_unitario': match.get('precio_unitario') if match else None,
                'match_proveedor': match.get('proveedor') if match else None,
                'match_descripcion': match.get('descripcion') if match else None,
                'match_score': round(score, 3),
                'match_type': match_type,
                'notas': self._generate_notes(carel_row, match, match_type)
            }
            
            results.append(result)
            
            if (idx + 1) % 100 == 0:
                logger.info(f"  Procesados {idx + 1} productos...")
        
        logger.info(f"✅ Matching completado: {len(results)} productos procesados")
        
        return pd.DataFrame(results)
    
    def _generate_notes(self, carel_row: Dict, match: Optional[Dict], match_type: str) -> str:
        """Genera notas descriptivas del matching."""
        
        if match_type == 'no_match':
            return "Sin coincidencia encontrada"
        
        if match_type == 'exact':
            return "Coincidencia perfecta - Todos los campos coinciden"
        
        if match_type == 'partial':
            notes = []
            
            if str(carel_row.get('paso', '')).lower() != str(match.get('paso', '')).lower():
                notes.append("Paso diferente")
            
            if str(carel_row.get('largo', '')).lower() != str(match.get('largo', '')).lower():
                notes.append("Largo aproximado")
            
            if str(carel_row.get('grado', '')).lower() != str(match.get('grado', '')).lower():
                notes.append("Grado diferente")
            
            return "; ".join(notes) if notes else "Match parcial"
        
        return ""