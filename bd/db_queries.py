from .db_connection import get_connection
import datetime
# Necesitamos importar el módulo de error para manejar excepciones específicas
import psycopg2 


# ------------------------------
# Insertar en EstadoTradicional
# ------------------------------
def insert_estado_tradicional(
    ventas, materia_prima, mano_obra, cif, total_costo_ventas, utilidad_bruta,
    salario_adm, salario_meseros, arrendamiento_oyv, depreciacion_oyv,
    industria_comercio, total_gastos_admon, utilidad_operacional
):
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        try:
            # Usar %s como marcador de posición para psycopg2
            cursor.execute("""
                INSERT INTO EstadoTradicional (
                    FechaGeneracion, Ventas, MateriaPrima, ManoDeObra, CIF,
                    TotalCostoVentas, UtilidadBruta, SalarioAdministracion, SalarioMeseros,
                    ArrendamientoOyV, DepreciacionOyV, IndustriaComercio,
                    TotalGastosAdmonVentas, UtilidadOperacional
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                datetime.datetime.now(), ventas, materia_prima, mano_obra, cif,
                total_costo_ventas, utilidad_bruta, salario_adm, salario_meseros,
                arrendamiento_oyv, depreciacion_oyv, industria_comercio,
                total_gastos_admon, utilidad_operacional
            ))
            conn.commit()
        except psycopg2.Error as e:
            conn.rollback()
            print(f"Error al insertar en EstadoTradicional: {e}")
        finally:
            cursor.close()
            conn.close()


# ------------------------------
# Insertar en EstadoVariable
# ------------------------------
def insert_estado_variable(
    ventas, costo_var_materia, costo_var_servicios, costo_var_comisiones,
    costo_var_industria, total_costos_var, margen_contribucion, costo_fijo_mano_obra,
    sueldo_fijo_adm, sueldo_fijo_meseros, arrendamiento, depreciacion,
    total_costos_fijos, utilidad_operacional, rentabilidad_ventas
):
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        try:
            # Usar %s como marcador de posición para psycopg2
            cursor.execute("""
                INSERT INTO EstadoVariable (
                    FechaGeneracion, Ventas, CostoVariableMateriaPrima, CostoVariableServiciosPublicos,
                    CostoVariableComisiones, CostoVariableIndustriaComercio, TotalCostosVariables,
                    MargenContribucion, CostoFijoManoObra, SueldoFijoAdministracion,
                    SueldoFijoMeseros, Arrendamiento, Depreciacion, TotalCostosFijos,
                    UtilidadOperacional, RentabilidadVentas
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                datetime.datetime.now(), ventas, costo_var_materia, costo_var_servicios,
                costo_var_comisiones, costo_var_industria, total_costos_var,
                margen_contribucion, costo_fijo_mano_obra, sueldo_fijo_adm,
                sueldo_fijo_meseros, arrendamiento, depreciacion, total_costos_fijos,
                utilidad_operacional, rentabilidad_ventas
            ))
            conn.commit()
        except psycopg2.Error as e:
            conn.rollback()
            print(f"Error al insertar en EstadoVariable: {e}")
        finally:
            cursor.close()
            conn.close()


# ------------------------------
# Insertar en PuntoEquilibrio
# ------------------------------
def insert_punto_equilibrio(
    pe_mes_unidades, pe_dia_unidades, pe_valor,
    margen_seg_porcent, margen_seg_valor,
    ventas_objetivo_unidades, ventas_objetivo_valor
):
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        try:
            # Usar %s como marcador de posición para psycopg2
            cursor.execute("""
                INSERT INTO PuntoEquilibrio (
                    FechaGeneracion, PuntoEquilibrioMesUnidades, PuntoEquilibrioDiaUnidades,
                    PuntoEquilibrioValor, MargenSeguridadPorc, MargenSeguridadValor,
                    VentasUtilidadObjetivoUnidades, VentasUtilidadObjetivoValor
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                datetime.datetime.now(), pe_mes_unidades, pe_dia_unidades,
                pe_valor, margen_seg_porcent, margen_seg_valor,
                ventas_objetivo_unidades, ventas_objetivo_valor
            ))
            conn.commit()
        except psycopg2.Error as e:
            conn.rollback()
            print(f"Error al insertar en PuntoEquilibrio: {e}")
        finally:
            cursor.close()
            conn.close()

    # Archivo: db_operations.py

# ... (tus funciones insert_estado_tradicional, etc., van aquí) ...

# -----------------------------------------------------------------
# Recuperar Reportes para Comparación
# -----------------------------------------------------------------

def get_available_reports():
    """
    Recupera una lista de tuplas (id, fecha_generacion) de todos los reportes
    guardados, ordenados por fecha descendente.
    """

    conn = get_connection()
    if not conn:
        return []
        
    cursor = conn.cursor()
    try:
        cursor.execute("""
             SELECT reporteid, FechaGeneracion
             FROM EstadoTradicional
             ORDER BY FechaGeneracion DESC
        """)
        
        # Devolvemos el resultado como una lista de tuplas (ID, Fecha)
        return cursor.fetchall() 
        
    except psycopg2.Error as e:
        print(f"Error al recuperar la lista de reportes: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def _fetch_data_from_table(cursor, table_name, report_id):
    """Función auxiliar para extraer datos de una sola tabla como diccionario."""
    
    # Usamos f-string para el nombre de la tabla (no inseguro ya que table_name está controlado)
    # y %s para el ReporteID
    cursor.execute(f"""
        SELECT *
        FROM {table_name}
        WHERE reporteid = %s  
    """, (report_id,)) # O WHERE id = %s, si usas 'id' en lugar de 'reporteid'
    
    # 🌟 PASO CRÍTICO: Mapear la tupla de resultado a un diccionario
    if cursor.rowcount > 0:
        col_names = [desc[0] for desc in cursor.description] # Obtiene los nombres de las columnas
        data = cursor.fetchone()                             # Obtiene la tupla de valores
        return dict(zip(col_names, data))                    # Mapea y devuelve el diccionario
    return None

def get_full_report_data(report_id):
    """
    Recupera todos los datos del Estado Tradicional, Estado Variable y PE
    para un ReporteID dado.
    """
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    try:
        data = {
            "tradicional": _fetch_data_from_table(cursor, "EstadoTradicional", report_id),
            "variable": _fetch_data_from_table(cursor, "EstadoVariable", report_id),
            "punto_equilibrio": _fetch_data_from_table(cursor, "PuntoEquilibrio", report_id),
        }
        return data
        
    except psycopg2.Error as e:
        print(f"Error al obtener datos del reporte {report_id}: {e}")
        return None
    finally:
        cursor.close()
        conn.close()