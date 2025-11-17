import random
import math

# --- Generación de Distribuciones ---

def triangular_variate(min_val, max_val, mode):
    """
    Genera un número aleatorio a partir de una distribución triangular.
    
    Args:
        min_val (float): Valor mínimo (a).
        max_val (float): Valor máximo (b).
        mode (float): Valor más probable (c).
        
    Returns:
        float: El valor aleatorio generado.
    """
    return random.triangular(min_val, max_val, mode)

def normal_variate(mu, sigma):
    """
    Genera un número aleatorio a partir de una distribución normal.
    
    Args:
        mu (float): Media (valor esperado).
        sigma (float): Desviación estándar.
        
    Returns:
        float: El valor aleatorio generado.
    """
    # Usa max(0, ...) para asegurar que el número de platos no sea negativo.
    return max(0, random.normalvariate(mu, sigma))

# --- Función de Generación de Datos de Simulación Principal ---

def generate_simulation_data(days, avg_lunches, sigma_lunches, avg_cost, min_cost, max_cost, mode_cost):
    """
    Genera series de tiempo simuladas para las variables clave.

    Args:
        days (int): Número de días a simular.
        avg_lunches (float): Media de almuerzos vendidos.
        sigma_lunches (float): Desviación estándar para almuerzos.
        avg_cost (float): Valor base del costo (usado como modo si no se especifica).
        min_cost (float): Mínimo costo de la carne (parámetro triangular).
        max_cost (float): Máximo costo de la carne (parámetro triangular).
        mode_cost (float): Modo (más probable) del costo (parámetro triangular).
        
    Returns:
        tuple: (lunches_data: list[float], cost_data: list[float])
    """
    lunches_data = []
    cost_data = []
    
    # 1. Simulación de Almuerzos Vendidos (Distribución Normal)
    for _ in range(days):
        lunches = normal_variate(avg_lunches, sigma_lunches)
        # Redondear a número entero de platos
        lunches_data.append(int(round(lunches)))
        
    # 2. Simulación de Costo de Carne (Distribución Triangular)
    # Definimos valores por defecto para la triangular si no son explícitos
    if not (min_cost and max_cost and mode_cost):
        mode_cost = avg_cost
        min_cost = avg_cost * 0.8  # Mínimo 20% menos
        max_cost = avg_cost * 1.2  # Máximo 20% más

    for _ in range(days):
        cost = triangular_variate(min_cost, max_cost, mode_cost)
        cost_data.append(round(cost, 2)) # Redondear a dos decimales
        
    return lunches_data, cost_data
