import pandas as pd
import logging
import os
from pathlib import Path
from .product_matcher import ProductMatcher

logger = logging.getLogger(__name__)


class MatchEngine:
    """
    Motor principal que orquesta el matching entre Carel y proveedores.
    """
    
    def __init__(self, threshold: float = 0.7):
        """
        Args:
            threshold: Score mínimo para considerar un match
        """
        self.matcher = ProductMatcher(threshold=threshold)
    
    def match_provider(self, 
                      carel_csv: str, 
                      provider_csv: str,
                      provider_name: str,
                      output_path: str = None) -> pd.DataFrame:
        """
        Hace matching de Carel contra un proveedor.
        
        Args:
            carel_csv: Ruta al CSV de Carel parseado
            provider_csv: Ruta al CSV del proveedor
            provider_name: Nombre del proveedor (para logs)
            output_path: Ruta donde guardar el CSV resultante (opcional)
            
        Returns:
            DataFrame con resultados
        """
        
        logger.info(f"\n{'='*60}")
        logger.info(f"MATCHING: Carel vs {provider_name.upper()}")
        logger.info(f"{'='*60}")
        
        # Cargar datos
        try:
            logger.info(f"📂 Cargando: {carel_csv}")
            carel_df = pd.read_csv(carel_csv)
            
            logger.info(f"📂 Cargando: {provider_csv}")
            provider_df = pd.read_csv(provider_csv)
            
        except FileNotFoundError as e:
            logger.error(f"❌ Archivo no encontrado: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"❌ Error al cargar datos: {e}")
            return pd.DataFrame()
        
        logger.info(f"   Carel: {len(carel_df)} productos")
        logger.info(f"   {provider_name}: {len(provider_df)} productos")
        
        # Ejecutar matching
        result_df = self.matcher.match_all(carel_df, provider_df)
        
        # Estadísticas
        self._print_stats(result_df, provider_name)
        
        # Guardar
        if output_path:
            try:
                # Crear directorio si no existe
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                result_df.to_csv(output_path, index=False, encoding='utf-8')
                logger.info(f"✅ Guardado en: {output_path}")
                
            except Exception as e:
                logger.error(f"❌ Error al guardar: {e}")
        
        return result_df
    
    def match_all_providers(self, 
                           carel_csv: str,
                           providers_dir: str,
                           output_dir: str = None) -> dict:
        """
        Hace matching de Carel contra múltiples proveedores.
        
        Args:
            carel_csv: Ruta al CSV de Carel parseado
            providers_dir: Directorio con los CSVs de proveedores
            output_dir: Directorio donde guardar los resultados
            
        Returns:
            Dict con {provider_name: result_df}
        """
        
        logger.info(f"\n{'#'*60}")
        logger.info(f"# MATCHING MÚLTIPLES PROVEEDORES")
        logger.info(f"#{'*'*58}")
        
        # Encontrar proveedores
        provider_files = list(Path(providers_dir).glob('*.csv'))
        
        if not provider_files:
            logger.error(f"❌ No se encontraron CSVs en {providers_dir}")
            return {}
        
        logger.info(f"📂 Encontrados {len(provider_files)} proveedores")
        
        results = {}
        
        for provider_file in provider_files:
            provider_name = provider_file.stem  # nombre sin extensión
            
            # Saltar algunos archivos si es necesario
            if '_match' in provider_name or provider_name == 'carel':
                continue
            
            output_path = None
            if output_dir:
                output_path = os.path.join(output_dir, f"{provider_name}_match.csv")
            
            try:
                result_df = self.match_provider(
                    carel_csv=carel_csv,
                    provider_csv=str(provider_file),
                    provider_name=provider_name,
                    output_path=output_path
                )
                
                results[provider_name] = result_df
                
            except Exception as e:
                logger.error(f"❌ Error procesando {provider_name}: {e}")
        
        logger.info(f"\n{'#'*60}")
        logger.info(f"# ✅ MATCHING COMPLETADO")
        logger.info(f"#{'*'*58}\n")
        
        return results
    
    def _print_stats(self, result_df: pd.DataFrame, provider_name: str):
        """Imprime estadísticas del matching."""
        
        if result_df.empty:
            logger.info("⚠️  Sin resultados")
            return
        
        total = len(result_df)
        exact = len(result_df[result_df['match_type'] == 'exact'])
        partial = len(result_df[result_df['match_type'] == 'partial'])
        no_match = len(result_df[result_df['match_type'] == 'no_match'])
        
        avg_score = result_df[result_df['match_type'] != 'no_match']['match_score'].mean()
        
        logger.info(f"\n📊 ESTADÍSTICAS DE MATCHING:")
        logger.info(f"   Total productos: {total}")
        logger.info(f"   ✅ Exact matches: {exact} ({100*exact/total:.1f}%)")
        logger.info(f"   ⚠️  Partial matches: {partial} ({100*partial/total:.1f}%)")
        logger.info(f"   ❌ No match: {no_match} ({100*no_match/total:.1f}%)")
        logger.info(f"   📈 Score promedio: {avg_score:.3f}")   