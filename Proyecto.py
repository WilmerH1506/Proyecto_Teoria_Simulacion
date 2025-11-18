import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import os
from Generacion_Variables import generate_simulation_data 
from export_pdf import exportar_simulacion_pdf
from bd.db_queries import insert_estado_tradicional, insert_estado_variable, insert_punto_equilibrio, get_available_reports, get_full_report_data
import threading

class ModernFinancialUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Simulación Financiera")
        self.root.geometry("1280x820")
        self.root.configure(bg="#ecf0f1")

        self.sidebar_width = 260
        self.sidebar_bg = "#1f2d3a"
        self.sidebar_btn_bg = "#273947"
        self.sidebar_btn_hover = "#314153"

        # ============================
        # 1. VARIABLES DE ENTRADA (Mantenidas)
        # ============================
        self.Entradas = {
            "Precio del Almuerzo": tk.DoubleVar(value=2500),
            "Dias trabajados al mes": tk.IntVar(value=22),
            "Almuerzos vendidos diariamente": tk.IntVar(value=120), # Simulado
        }

        self.Entradas_Personal = {
            "Cocineros": {
                "Salario Base": tk.DoubleVar(value=750000),
                "Cantidad de Cocineros": tk.IntVar(value=1),
            },
            "Ayudantes de Cocina": {
                "Salario Base": tk.DoubleVar(value=600000),
                "Cantidad de Ayudantes de Cocina": tk.IntVar(value=2),
            },
            "Meseros": {
                "Salario Base": tk.DoubleVar(value=300000),
                "Cantidad de Meseros": tk.IntVar(value=3),
            },
            "Administradores": {
                "Salario Base": tk.DoubleVar(value=200000),
                "Cantidad de Administradores": tk.IntVar(value=1),
            },
        }
        self.Factor_Prestacional = tk.DoubleVar(value=0.52)

        self.insumos = {
            "Arroz": {
                "Precio Kilo": tk.DoubleVar(value=50),
                "Cantidad (g)": tk.DoubleVar(value=45),
            },
            "Carne": {
                "Precio Kilo": tk.DoubleVar(value=150),
                "Cantidad (g)": tk.DoubleVar(value=200),
            },
            "Papa": {
                "Precio Kilo": tk.DoubleVar(value=200),
                "Cantidad (g)": tk.DoubleVar(value=70),
            },
            "Maduro y otros": {
                "Precio Kilo": tk.DoubleVar(value=75),
                "Cantidad (g)": tk.DoubleVar(value=45),
            },
        }
        
        self.GastosGenerales = {
            "Arriendo": tk.DoubleVar(value=900000),
            "Servicios Públicos": tk.DoubleVar(value=50),
            "Industria y Comercio": tk.DoubleVar(value=0.005),
            "Depreciacion": tk.DoubleVar(value=250000),
        }

        self.SIM_PARAMS = {
            "Dias": 100,
            "Sigma Almuerzos": 15,
            "Carne Min": 750,
            "Carne Max": 1150,
            "Carne Mode": 900
        }
        
        self.ASIGNACION = {
            "Arriendo_Ventas": 0.80,
            "Arriendo_Cocina": 0.20,
            "Depreciacion_Ventas": 0.50,
            "Depreciacion_Cocina": 0.50,
        }

        # ============================
        # 2. VARIABLES CALCULADAS (Mantenidas)
        # ============================
        self.personal_calculated_vars = {}
        for puesto in self.Entradas_Personal.keys():
            self.personal_calculated_vars[puesto] = {
                "Salario": tk.DoubleVar(value=0.0),
                "Comisiones": tk.DoubleVar(value=0.0),
                "Prestaciones": tk.DoubleVar(value=0.0),
                "Total": tk.DoubleVar(value=0.0),
            }
        
        self.ventas_totales_mensuales = tk.DoubleVar(value=0.0)

        # ============================
        # 3. INICIALIZACIÓN Y TRAZADO (Mantenidas)
        # ============================
        self._calculate_sales_and_personnel_costs()
        self._setup_variable_tracing()

        self.create_sidebar()
        self.create_main_area()
        self.show_dashboard()
        
    def _calculate_sales_and_personnel_costs(self):
        """Calcula las ventas mensuales y los costos de personal."""
        # Lógica mantenida
        try:
            precio_almuerzo = self.Entradas["Precio del Almuerzo"].get()
            dias_trabajados = self.Entradas["Dias trabajados al mes"].get()
            almuerzos_diarios = self.Entradas["Almuerzos vendidos diariamente"].get() 
            factor_prestacional = self.Factor_Prestacional.get()

            ventas_totales = precio_almuerzo * almuerzos_diarios * dias_trabajados
            self.ventas_totales_mensuales.set(ventas_totales)
            
            for puesto, datos_entrada in self.Entradas_Personal.items():
                datos_salida = self.personal_calculated_vars[puesto]
                
                salario_base_unitario = datos_entrada["Salario Base"].get()
                cantidad = datos_entrada["Cantidad de " + puesto].get()
                
                costo_base_mensual = salario_base_unitario * cantidad
                datos_salida["Salario"].set(costo_base_mensual)
                
                comisiones = 0.0
                if "Meseros" in puesto:
                    comisiones = ventas_totales * 0.01 
                elif "Administradores" in puesto:
                    comisiones = ventas_totales * 0.10
                
                datos_salida["Comisiones"].set(comisiones)

                base_prestaciones = costo_base_mensual + comisiones
                prestaciones = base_prestaciones * factor_prestacional
                datos_salida["Prestaciones"].set(prestaciones)
                
                total = costo_base_mensual + comisiones + prestaciones
                datos_salida["Total"].set(total)
                
        except tk.TclError:
            pass
            
    def _setup_variable_tracing(self):
        """Configura el rastreo de cambios."""
        # Lógica mantenida
        relevant_vars = []
        relevant_vars.extend(self.Entradas.values())
        for datos in self.Entradas_Personal.values():
            relevant_vars.extend(datos.values())
        relevant_vars.append(self.Factor_Prestacional)
        for datos in self.insumos.values():
            relevant_vars.extend(datos.values())
        relevant_vars.extend(self.GastosGenerales.values())
        
        for var in relevant_vars:
            var.trace_add("write", lambda name, index, mode: self._calculate_sales_and_personnel_costs())

    def _calculate_traditional_statement(self):
        """Calcula todos los rubros del Estado de Resultados Tradicional."""
        ventas_mensuales = self.ventas_totales_mensuales.get() 
        almuerzos_mensuales = self.Entradas["Almuerzos vendidos diariamente"].get() * self.Entradas["Dias trabajados al mes"].get()
        dias_trabajados = self.Entradas["Dias trabajados al mes"].get()
        statement = {}
        try:
            insumos_arroz = self.insumos["Arroz"]["Precio Kilo"].get() * (self.insumos["Arroz"]["Cantidad (g)"].get() / 1000)
            insumos_carne = self.insumos["Carne"]["Precio Kilo"].get() * (self.insumos["Carne"]["Cantidad (g)"].get() / 1000)
            insumos_papa = self.insumos["Papa"]["Precio Kilo"].get() * (self.insumos["Papa"]["Cantidad (g)"].get() / 1000)
            insumos_maduro = self.insumos["Maduro y otros"]["Precio Kilo"].get() * (self.insumos["Maduro y otros"]["Cantidad (g)"].get() / 1000)
            total_insumos_por_almuerzo = insumos_arroz + insumos_carne + insumos_papa + insumos_maduro
            materia_prima = total_insumos_por_almuerzo * almuerzos_mensuales
            mod_cocineros = self.personal_calculated_vars["Cocineros"]["Total"].get()
            mod_ayudantes = self.personal_calculated_vars["Ayudantes de Cocina"]["Total"].get()
            mano_obra = mod_cocineros + mod_ayudantes
            arriendo_local = self.GastosGenerales["Arriendo"].get()
            arriendo_cif = arriendo_local * self.ASIGNACION["Arriendo_Cocina"]
            sp_unitario = self.GastosGenerales["Servicios Públicos"].get() 
            almuerzos_diarios = self.Entradas["Almuerzos vendidos diariamente"].get()
            sp_cif = sp_unitario * almuerzos_diarios * dias_trabajados
            depreciacion_equipos = self.GastosGenerales["Depreciacion"].get()
            depreciacion_cif = depreciacion_equipos * self.ASIGNACION["Depreciacion_Cocina"]
            cif_total = arriendo_cif + sp_cif + depreciacion_cif
            total_costo_ventas = materia_prima + mano_obra + cif_total
            utilidad_bruta = ventas_mensuales - total_costo_ventas
            salario_adm = self.personal_calculated_vars["Administradores"]["Total"].get()
            salario_meseros = self.personal_calculated_vars["Meseros"]["Total"].get()
            arriendo_oyv = arriendo_local * self.ASIGNACION["Arriendo_Ventas"]
            depreciacion_oyv = depreciacion_equipos * self.ASIGNACION["Depreciacion_Ventas"]
            ic_tasa = self.GastosGenerales["Industria y Comercio"].get()
            ic_oyv = ic_tasa * ventas_mensuales
            total_gastos_oyv = salario_adm + salario_meseros + arriendo_oyv + depreciacion_oyv + ic_oyv
            utilidad_operacional = utilidad_bruta - total_gastos_oyv
            
            # Poblar el diccionario (asumo que las ventas no son cero, si no, salta la excepción)
            statement["Ventas"] = (ventas_mensuales, 1.0)
            statement["Materia Prima"] = (materia_prima, materia_prima / ventas_mensuales)
            statement["Mano de Obra Directa"] = (mano_obra, mano_obra / ventas_mensuales)
            statement["CIF"] = (cif_total, cif_total / ventas_mensuales)
            statement["Total Costo de Ventas"] = (total_costo_ventas, total_costo_ventas / ventas_mensuales)
            statement["Utilidad Bruta en Ventas"] = (utilidad_bruta, utilidad_bruta / ventas_mensuales)
            statement["Salario Administración"] = (salario_adm, salario_adm / ventas_mensuales)
            statement["Salario Meseros"] = (salario_meseros, salario_meseros / ventas_mensuales)
            statement["Arrendamiento (OyV)"] = (arriendo_oyv, arriendo_oyv / ventas_mensuales)
            statement["Depreciación (OyV)"] = (depreciacion_oyv, depreciacion_oyv / ventas_mensuales)
            statement["Industria y Comercio"] = (ic_oyv, ic_oyv / ventas_mensuales)
            statement["Total Gastos Admon y Ventas"] = (total_gastos_oyv, total_gastos_oyv / ventas_mensuales)
            statement["Utilidad Operacional"] = (utilidad_operacional, utilidad_operacional / ventas_mensuales)


            def insertar():
                try:
                    insert_estado_tradicional(
                        ventas_mensuales, materia_prima, mano_obra, cif_total, total_costo_ventas,
                        utilidad_bruta, salario_adm, salario_meseros, arriendo_oyv,
                        depreciacion_oyv, ic_oyv, total_gastos_oyv, utilidad_operacional
                    )
                except Exception as e:
                    print(f"Error al insertar Estado Tradicional: {e}")

            threading.Thread(target=insertar).start()

            return statement

        except ZeroDivisionError:
            messagebox.showerror("Error de Cálculo", "Las ventas no pueden ser cero. Verifique las variables de entrada.")
            return None
        except Exception as e:
            messagebox.showerror("Error de Cálculo", f"Error en el cálculo del Estado de Resultados Tradicional: {e}")
            return None

    def _calculate_variable_statement(self):
        """
        Calcula el Estado de Resultados por Costo Variable (o Marginal).
        """
        try:
            ventas_totales = self.ventas_totales_mensuales.get()
            
            # --- 1. CÁLCULO DE COSTOS VARIABLES ---
            
            # A. Costo Variable de Materia Prima (Insumos)
            almuerzos_diarios = self.Entradas["Almuerzos vendidos diariamente"].get()
            dias_trabajados = self.Entradas["Dias trabajados al mes"].get()
            almuerzos_mensuales = almuerzos_diarios * dias_trabajados
            
            costo_materia_prima_unidad = 0.0
            for _, datos in self.insumos.items():
                precio_kilo = datos["Precio Kilo"].get()
                cantidad_g = datos["Cantidad (g)"].get()
                costo_materia_prima_unidad += (precio_kilo * cantidad_g) / 1000 
                
            total_materia_prima = costo_materia_prima_unidad * almuerzos_mensuales

            # B. Costo Variable de servicios publicos (proporcional a almuerzos vendidos)
            sp = self.GastosGenerales["Servicios Públicos"].get()
            total_sp = sp * dias_trabajados * almuerzos_diarios
            

            # C. Costo Variable de Comisiones (Meseros y Administradores)
            total_comisiones = sum(
                datos["Comisiones"].get() 
                for datos in self.personal_calculated_vars.values()
            )
            factor_prestacional = self.Factor_Prestacional.get()
            comisiones_sobre_ventas = total_comisiones * (1 + factor_prestacional)
            
            # D. Costo Variable de Impuesto (Industria y Comercio)
            ind_y_com = self.GastosGenerales["Industria y Comercio"].get()
            total_ind_y_com = ventas_totales * ind_y_com

            # D. Total Costos Variables
            total_costos_variables = total_materia_prima + total_sp + comisiones_sobre_ventas + total_ind_y_com
            
            # --- 2. CÁLCULO DEL MARGEN DE CONTRIBUCIÓN ---
            margen_contribucion = ventas_totales - total_costos_variables
            
            # --- 3. CÁLCULO DE COSTOS FIJOS ---
            
            # A. Costo Fijo de Mano de Obra (Salarios cocineros y ayudantes)
            mano_obra_fija = sum(
                self.personal_calculated_vars[puesto]["Total"].get()
                for puesto in ["Cocineros", "Ayudantes de Cocina"]
            )

            # B. Sueldo Fijo (Administracion)
            SalarioAdmin = self.personal_calculated_vars["Administradores"]["Salario"].get()
            SalarioFijoAdmin = SalarioAdmin * (1 + factor_prestacional)
            
            # C. Sueldo Fijo (Meseros)
            SalarioMeseros = self.personal_calculated_vars["Meseros"]["Salario"].get()
            SalarioFijoMeseros = SalarioMeseros * (1 + factor_prestacional)
            
            # D. Arrendamiento local
            arriendo = self.GastosGenerales["Arriendo"].get()

            # E. Depreciación equipos
            depreciacion = self.GastosGenerales["Depreciacion"].get()

            total_costos_fijos = mano_obra_fija + SalarioFijoAdmin + SalarioFijoMeseros + arriendo + depreciacion
            
            # --- 4. CÁLCULO DE UTILIDAD OPERACIONAL ---
            utilidad_operacional = margen_contribucion - total_costos_fijos

            Rentabilidad_en_ventas = utilidad_operacional / ventas_totales if ventas_totales else 0
            
            # --- 5. Estructura de Salida ---


            def insertar():
                try:
                    insert_estado_variable(
                        ventas_totales, total_materia_prima, total_sp,
                        comisiones_sobre_ventas, total_ind_y_com,
                        total_costos_variables, margen_contribucion,
                        mano_obra_fija, SalarioFijoAdmin, SalarioFijoMeseros,
                        arriendo, depreciacion, total_costos_fijos,
                        utilidad_operacional, Rentabilidad_en_ventas
                    )
                except Exception as e:
                    print(f"Error al insertar Estado Variable: {e}")
                
            threading.Thread(target=insertar).start()
            
            results = {
                "Ventas": (ventas_totales, 1.0),
                "Costo Variable de Materia Prima": (total_materia_prima, total_materia_prima / ventas_totales if ventas_totales else 0),
                "Costo Variable de Servicios Públicos": (total_sp, total_sp / ventas_totales if ventas_totales else 0),
                "Costo Variable de Comisiones": (comisiones_sobre_ventas, comisiones_sobre_ventas / ventas_totales if ventas_totales else 0),
                "Costo Variable de Industria y Comercio": (total_ind_y_com, total_ind_y_com / ventas_totales if ventas_totales else 0),

                "Total Costos Variables": (total_costos_variables, total_costos_variables / ventas_totales if ventas_totales else 0),
                "Margen de Contribución": (margen_contribucion, margen_contribucion / ventas_totales if ventas_totales else 0),

                "Costo Fijo de Mano de Obra": (mano_obra_fija, mano_obra_fija / ventas_totales if ventas_totales else 0),
                "Sueldo Fijo Administración": (SalarioFijoAdmin, SalarioFijoAdmin / ventas_totales if ventas_totales else 0),
                "Sueldo Fijo Meseros": (SalarioFijoMeseros, SalarioFijoMeseros / ventas_totales if ventas_totales else 0),
                "Arrendamiento": (arriendo, arriendo / ventas_totales if ventas_totales else 0),
                "Depreciación": (depreciacion, depreciacion / ventas_totales if ventas_totales else 0),

                "Total Costos Fijos": (total_costos_fijos, total_costos_fijos / ventas_totales if ventas_totales else 0),
                "Utilidad Operacional": (utilidad_operacional, Rentabilidad_en_ventas),

                "Rentabilidad en Ventas": (Rentabilidad_en_ventas, Rentabilidad_en_ventas),
            }

            # -------------------- Punto de Equilibrio --------------------
            costo_variable_unitario = total_costos_variables / almuerzos_mensuales if almuerzos_mensuales else 0
            precio_plato = self.Entradas["Precio del Almuerzo"].get()
            margen_contribucion_unitario =  precio_plato - costo_variable_unitario if almuerzos_mensuales else 0

            Punto_Equilibrio_Mes = total_costos_fijos / (precio_plato - costo_variable_unitario) if (precio_plato - costo_variable_unitario) else 0
            Punto_Equilibrio_Dia = Punto_Equilibrio_Mes / dias_trabajados if dias_trabajados else 0
            Punto_Equilibrio_Unidades = Punto_Equilibrio_Mes * precio_plato if precio_plato else 0

            margen_seguridad = (almuerzos_mensuales - Punto_Equilibrio_Mes) / almuerzos_mensuales if almuerzos_mensuales else 0
            margen_seguridad_valor = ventas_totales - Punto_Equilibrio_Unidades if ventas_totales else 0

            utilidad_objetivo = 2500000

            Ventas_Mensuales_unidades = (utilidad_objetivo + total_costos_fijos) / (precio_plato - costo_variable_unitario) if (precio_plato - costo_variable_unitario) else 0
            almuerzos_diarios = Ventas_Mensuales_unidades / dias_trabajados if dias_trabajados else 0
            Ventas_Mensuales_valor = Ventas_Mensuales_unidades * precio_plato if precio_plato else 0

            results.update({
                "Punto de Equilibrio (Mes - Unidades)": (Punto_Equilibrio_Mes, Punto_Equilibrio_Mes / almuerzos_mensuales if almuerzos_mensuales else 0),
                "Punto de Equilibrio (Día - Unidades)": (Punto_Equilibrio_Dia, Punto_Equilibrio_Dia / almuerzos_diarios if almuerzos_diarios else 0),
                "Punto de Equilibrio (Valor)": (Punto_Equilibrio_Unidades, Punto_Equilibrio_Unidades / ventas_totales if ventas_totales else 0),
                "Margen de Seguridad (%)": (margen_seguridad, margen_seguridad),
                "Margen de Seguridad (Valor)": (margen_seguridad_valor, margen_seguridad_valor / ventas_totales if ventas_totales else 0),
                "Ventas para Utilidad Objetivo (Unidades)": (Ventas_Mensuales_unidades, Ventas_Mensuales_unidades / almuerzos_mensuales if almuerzos_mensuales else 0),
                "Ventas para Utilidad Objetivo (Valor)": (Ventas_Mensuales_valor, Ventas_Mensuales_valor / ventas_totales if ventas_totales else 0),
            })

            def insertar_pe():
                try:
                    insert_punto_equilibrio(
                        Punto_Equilibrio_Mes, Punto_Equilibrio_Dia, Punto_Equilibrio_Unidades,
                        margen_seguridad, margen_seguridad_valor,
                        Ventas_Mensuales_unidades, Ventas_Mensuales_valor
                    )
                except Exception as e:
                    print(f"Error al insertar Punto de Equilibrio: {e}")

            threading.Thread(target=insertar_pe).start()
            
            return results
            
        except tk.TclError as e:
            print(f"Error en cálculo de costo variable: {e}")
            return None
    
    def _execute_comparison_logic(self):
        """
        Obtiene los ReporteIDs seleccionados, usa datos estáticos, y genera la vista 
        de comparación con pestañas, ajustando el tamaño del contenedor.
        """
        
        # 1. Limpiar el área de resultados anterior
        for widget in self.comparison_results_frame.winfo_children():
            widget.destroy()

        # 📝 DATOS ESTÁTICOS DE EJEMPLO (Simulando la estructura de la base de datos)
        STATIC_DATA_REPORT_A = {
            "tradicional": {
                "Ventas": 1500000, "MateriaPrima": 300000, "ManoDeObra": 100000, "CIF": 50000,
                "TotalCostoVentas": 450000, "UtilidadBruta": 1050000, "SalarioAdministracion": 80000,
                "TotalGastosAdmonVentas": 120000, "UtilidadOperacional": 930000,
            },
            "variable": {
                "Ventas": 1500000, "TotalCostosVariables": 500000, "MargenContribucion": 1000000,
                "TotalCostosFijos": 250000, "UtilidadOperacional": 750000, "RentabilidadVentas": 0.50,
            },
            "punto_equilibrio": {
                "PuntoEquilibrioValor": 500000, "PuntoEquilibrioMesUnidades": 1000, "PuntoEquilibrioDiaUnidades": 33.33,
                "MargenSeguridadPorc": 0.66, "VentasUtilidadObjetivoValor": 1200000,
            },
        }

        STATIC_DATA_REPORT_B = {
            "tradicional": {
                "Ventas": 1800000, "MateriaPrima": 350000, "ManoDeObra": 120000, "CIF": 60000,
                "TotalCostoVentas": 530000, "UtilidadBruta": 1270000, "SalarioAdministracion": 80000,
                "TotalGastosAdmonVentas": 130000, "UtilidadOperacional": 1140000,
            },
            "variable": {
                "Ventas": 1800000, "TotalCostosVariables": 600000, "MargenContribucion": 1200000,
                "TotalCostosFijos": 250000, "UtilidadOperacional": 950000, "RentabilidadVentas": 0.527,
            },
            "punto_equilibrio": {
                "PuntoEquilibrioValor": 500000, "PuntoEquilibrioMesUnidades": 1000, "PuntoEquilibrioDiaUnidades": 33.33,
                "MargenSeguridadPorc": 0.72, "VentasUtilidadObjetivoValor": 1400000,
            },
        }

        # 2. Extracción y Validación de ReporteIDs
        try:
            report1_id = int(self.report1_var.get().split(' ')[1])
            report2_id = int(self.report2_var.get().split(' ')[1])
        except Exception as e:
            messagebox.showerror("Error de Selección", f"Fallo al leer el ID del reporte. Error: {e}")
            return

        if report1_id == report2_id:
            tk.Label(self.comparison_results_frame, 
                    text="⚠️ Por favor, selecciona dos reportes diferentes para comparar.",
                    font=("Segoe UI", 11), fg="#f39c12").pack(pady=10)
            return

        # Asignación de datos estáticos
        data1 = STATIC_DATA_REPORT_A
        data2 = STATIC_DATA_REPORT_B

        # 3. Configurar la vista con Pestañas (Notebook)
        
        tk.Label(self.comparison_results_frame, text="Indicadores Clave", 
                font=("Segoe UI", 14, "bold"), bg="#ecf0f1").pack(pady=(10, 5))

        notebook = ttk.Notebook(self.comparison_results_frame)
        # Importante: No usar fill/expand para que se ajuste al contenido.
        notebook.pack(padx=10, pady=10) 

        # Crear frames para cada estado
        tradicional_comp_frame = tk.Frame(notebook, bg="white")
        variable_comp_frame = tk.Frame(notebook, bg="white")
        pe_comp_frame = tk.Frame(notebook, bg="white")
        
        # Empaquetamos los frames (necesario si el notebook usa grid o pack con fill)
        tradicional_comp_frame.pack(fill="both")
        variable_comp_frame.pack(fill="both")
        pe_comp_frame.pack(fill="both")

        # Añadir pestañas
        notebook.add(tradicional_comp_frame, text="Costo Tradicional ⚖️")
        notebook.add(variable_comp_frame, text="Costo Variable ⚖️")
        notebook.add(pe_comp_frame, text="Punto de Equilibrio ⚖️")

        # 4. Dibujar las tablas
        self._draw_comparison_table(tradicional_comp_frame, data1, data2, report1_id, report2_id, "tradicional")
        self._draw_comparison_table(variable_comp_frame, data1, data2, report1_id, report2_id, "variable")
        self._draw_comparison_table(pe_comp_frame, data1, data2, report1_id, report2_id, "punto_equilibrio")
    
    def create_sidebar(self):
        self.sidebar_frame = tk.Frame(self.root, bg=self.sidebar_bg, width=self.sidebar_width)
        self.sidebar_frame.place(x=0, y=0, relheight=1, width=self.sidebar_width) # Usar width y relheight

        tk.Label(self.sidebar_frame, text="Simulador Financiero", fg="white",
                  bg=self.sidebar_bg, font=("Segoe UI", 14, "bold")).place(x=30, y=24)

        buttons = [
            ("Dashboard", self.show_dashboard),
            ("Simulación", self.show_simulation_view),
            ("Comparar Estados", self.show_comparison_view),
        ]

        y = 110
        for text, cmd in buttons:
            self.create_sidebar_button(text, cmd, y)
            y += 64

    def create_sidebar_button(self, text, command, y):
        btn = tk.Button(
            self.sidebar_frame, text=text, anchor="w",
            command=command, bg=self.sidebar_btn_bg, fg="white",
            activebackground=self.sidebar_btn_hover, activeforeground="white",
            bd=0, relief="flat", padx=20, font=("Segoe UI", 12)
        )
        btn.place(x=10, y=y, width=self.sidebar_width - 20, height=50)
        btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=self.sidebar_btn_hover))
        btn.bind("<Leave>", lambda e, b=btn: b.configure(bg=self.sidebar_btn_bg))

    def create_main_area(self):
        # *** CORRECCIÓN CLAVE 1: Usamos place con x y relwidth, o mejor, simplemente pack/grid para el main_frame
        # Al usar place, necesitamos asegurarnos de que el ancho sea relativo al padre (root)
        self.main_frame = tk.Frame(self.root, bg="#ecf0f1")
        # Ajustamos el main_frame para que ocupe el espacio restante:
        self.main_frame.place(x=self.sidebar_width, y=0, relwidth=1.0, relheight=1.0, width=-self.sidebar_width)
        
    def clear_main(self):
        for w in self.main_frame.winfo_children():
            w.destroy()

    def _create_input_sections(self, parent_frame, left_col, right_col):
        """Crea y empaqueta todas las secciones de entrada en las columnas provistas."""

        # Lógica de creación de Inputs (Mantenida)
        
        # 1. ENTRADAS
        ent_frame = tk.LabelFrame(left_col, text="Entradas Generales",
                                     font=("Segoe UI", 12, "bold"), bg="white", padx=5, pady=5)
        ent_frame.pack(fill="x", pady=10)
        for entrada, var in self.Entradas.items():
            row = tk.Frame(ent_frame, bg="white")
            row.pack(fill="x", pady=4, padx=8)
            tk.Label(row, text=entrada, width=25, anchor="w", bg="white").pack(side="left")
            tk.Entry(row, textvariable=var, width=12, justify='right').pack(side="right", padx=(5, 0))

        # 2. Entradas Personal
        ep_frame = tk.LabelFrame(left_col, text="Entradas Personal",
                                     font=("Segoe UI", 12, "bold"), bg="white", padx=5, pady=5)
        ep_frame.pack(fill="x", pady=10)

        header_ep = tk.Frame(ep_frame, bg="#f0f0f0")
        header_ep.pack(fill="x", pady=(0, 5), padx=8)
        tk.Label(header_ep, text="Puesto", bg="#f0f0f0", font=("Segoe UI", 10, "bold"), width=20, anchor="w").pack(side="left")
        tk.Label(header_ep, text="Cantidad", bg="#f0f0f0", font=("Segoe UI", 10, "bold"), width=12, anchor="e").pack(side="right", padx=(5, 0))
        tk.Label(header_ep, text="Salario Base", bg="#f0f0f0", font=("Segoe UI", 10, "bold"), width=12, anchor="e").pack(side="right", padx=(5, 0))

        for puesto, datos in self.Entradas_Personal.items():
            row = tk.Frame(ep_frame, bg="white")
            row.pack(fill="x", pady=4, padx=8)
            tk.Label(row, text=puesto, width=20, anchor="w", bg="white").pack(side="left")
            tk.Entry(row, textvariable=datos["Salario Base"], width=12, justify='right').pack(side="right", padx=(5, 0))
            tk.Entry(row, textvariable=datos["Cantidad de " + puesto], width=12, justify='right').pack(side="right", padx=(5, 0))
            
        row = tk.Frame(ep_frame, bg="white")
        row.pack(fill="x", pady=4, padx=8)
        tk.Label(row, text="Factor prestacional", width=20, anchor="w", bg="white").pack(side="left")
        tk.Entry(row, textvariable=self.Factor_Prestacional, width=12, justify='right').pack(side="right", padx=(5, 0))


        # 3. INSUMOS
        ins_frame = tk.LabelFrame(right_col, text="Insumos",
                                        font=("Segoe UI", 12, "bold"), bg="white", padx=5, pady=5)
        ins_frame.pack(fill="x", pady=10)
        header_ins = tk.Frame(ins_frame, bg="#f0f0f0")
        header_ins.pack(fill="x", pady=(0, 5), padx=8)
        tk.Label(header_ins, text="Insumo", bg="#f0f0f0", font=("Segoe UI", 10, "bold"), width=20, anchor="w").pack(side="left")
        tk.Label(header_ins, text="Cantidad (g)", bg="#f0f0f0", font=("Segoe UI", 10, "bold"), width=20, anchor="e").pack(side="right", padx=(5, 0))
        tk.Label(header_ins, text="Precio Kilo", bg="#f0f0f0", font=("Segoe UI", 10, "bold"), width=12, anchor="e").pack(side="right", padx=(5, 0))
        for insumo, datos in self.insumos.items():
            row = tk.Frame(ins_frame, bg="white")
            row.pack(fill="x", pady=4, padx=8)
            tk.Label(row, text=insumo, width=20, anchor="w", bg="white").pack(side="left")
            tk.Entry(row, textvariable=datos["Precio Kilo"], width=12, justify='right').pack(side="right", padx=(5, 0))
            tk.Entry(row, textvariable=datos["Cantidad (g)"], width=20, justify='right').pack(side="right", padx=(5, 0))
            
            
        # 5. Gastos Generales
        gg_frame = tk.LabelFrame(right_col, text="Gastos Generales",
                                     font=("Segoe UI", 12, "bold"), bg="white", padx=5, pady=5)
        gg_frame.pack(fill="x", pady=10)
        for gasto, var in self.GastosGenerales.items():
            row = tk.Frame(gg_frame, bg="white")
            row.pack(fill="x", pady=4, padx=8)
            tk.Label(row, text=gasto, width=20, anchor="w", bg="white").pack(side="left")
            tk.Entry(row, textvariable=var, width=12, justify='right').pack(side="right", padx=(5, 0))

        return self._create_personnel_cost_table(parent_frame)
    
    def _create_personnel_cost_table(self, parent_frame):
        # Lógica mantenida
        per_frame = tk.LabelFrame(parent_frame, text="Costo Total de Personal (Calculado)",
                                     font=("Segoe UI", 12, "bold"), bg="white")
        per_frame.pack(fill="x", padx=20, pady=10) 
        header = tk.Frame(per_frame, bg="#f0f0f0")
        header.pack(fill="x", pady=5, padx=8)
        tk.Label(header, text="Puesto", bg="#f0f0f0", font=("Segoe UI", 10, "bold"), width=15, anchor="w").pack(side="left", padx=(0, 3))
        for txt in ["Salario", "Comisiones", "Prestaciones", "Total"]:
            tk.Label(header, text=txt, bg="#f0f0f0", font=("Segoe UI", 10, "bold"), anchor="e").pack(side="left", padx=5, fill="x", expand=True)

        for puesto, datos in self.personal_calculated_vars.items():
            row = tk.Frame(per_frame, bg="white")
            row.pack(fill="x", pady=3, padx=8)
            tk.Label(row, text=puesto, width=15, bg="white", anchor="w").pack(side="left", padx=(0,0))
            for key in ["Salario", "Comisiones", "Prestaciones", "Total"]:
                entry = tk.Entry(row, textvariable=datos[key], width=15, justify='right', 
                                 state='readonly', relief="flat", bg="#e8f0f7", fg="#2c3e50", font=("Segoe UI", 10))
                entry.pack(side="left", padx=(5, 5), fill="x", expand=True)
                
        return per_frame

    def _generate_and_plot_random_data(self, scroll_frame):
        """
        Genera datos simulados, actualiza variables de Tkinter y plotea la serie de tiempo.
        Añade líneas de referencia para Mínimo, Máximo y Valor Final establecido.
        """
        plot_frame = tk.LabelFrame(scroll_frame, text="Gráfica de Simulación Dinámica (30 Días)",
                                     font=("Segoe UI", 12, "bold"), bg="white")
        plot_frame.pack(fill="x", padx=20, pady=10)

        # Definiciones de Canvas
        canvas_width = 900
        canvas_height = 400 # Aumentado para mejor visualización
        canvas = tk.Canvas(plot_frame, width=canvas_width, height=canvas_height, bg="#f7f7f7", bd=1, relief="solid")
        canvas.pack(padx=10, pady=10)

        days = self.SIM_PARAMS["Dias"]
        margin = 60 # Aumentado para etiquetas en el Eje Y
        x_scale = (canvas_width - 2 * margin) / (days - 1)
        
        # Formato de números enteros con separadores de miles
        formato_float = lambda x: f"{x:,.2f}"

        try:
            # --- 1. Generación de Datos Usando el Motor de Simulación ---
            avg_lunches = self.Entradas["Almuerzos vendidos diariamente"].get()
            avg_price_kilo = self.insumos["Carne"]["Precio Kilo"].get()
            
            lunches_data, cost_data = generate_simulation_data(
                days=days,
                avg_lunches=avg_lunches,
                sigma_lunches=self.SIM_PARAMS["Sigma Almuerzos"],
                avg_cost=avg_price_kilo,
                min_cost=self.SIM_PARAMS["Carne Min"],
                max_cost=self.SIM_PARAMS["Carne Max"],
                mode_cost=self.SIM_PARAMS["Carne Mode"]
            )
            
            # --- 2. Obtener Valores de Referencia ---
            min_lunches = min(lunches_data)
            max_lunches = max(lunches_data)
            
            min_cost = min(cost_data)
            max_cost = max(cost_data)
            
            # Valores finales actualizados por la simulación
            final_lunches = lunches_data[-1] 
            final_cost = cost_data[-1] 

            self.Entradas["Almuerzos vendidos diariamente"].set(final_lunches)
            self.insumos["Carne"]["Cantidad (g)"].set(final_cost)

            # --- 3. Preparación de Ejes y Escala para el plot ---
            
            # Escala Vertical (Eje Y): Incluir TODOS los datos (almuerzos y costos)
            min_y_data = min(min(lunches_data), min(cost_data))
            max_y_data = max(max(lunches_data), max(cost_data))
            
            # Ajuste de margen para la escala del eje Y (5% de buffer)
            min_y = min_y_data * 0.95
            max_y = max_y_data * 1.05
            y_range = max_y - min_y
            y_scale = (canvas_height - 2 * margin) / y_range

            # Dibujar Ejes
            canvas.create_line(margin, canvas_height - margin, canvas_width - margin, canvas_height - margin, fill="gray") # Eje X
            canvas.create_line(margin, margin, margin, canvas_height - margin, fill="gray") # Eje Y
            
            # Etiquetas del Eje X
            for i in range(days):
                if i % 5 == 0 or i == days - 1:
                    x = margin + i * x_scale
                    canvas.create_text(x, canvas_height - margin + 15, text=str(i + 1), fill="gray", anchor="n")
            canvas.create_text(canvas_width / 2, canvas_height - 5, text="Días de Simulación (1-30)", fill="#2c3e50", font=("Segoe UI", 10, "bold"))
            
            # --- 4. Etiquetas y Cuadrícula del Eje Y ---
            num_labels = 7 # 7 puntos de referencia
            
            def to_canvas_y(value):
                """Convierte un valor de datos a una coordenada Y del canvas."""
                return canvas_height - margin - (value - min_y) * y_scale
                
            # Generar etiquetas del Eje Y
            for i in range(num_labels):
                value = min_y + (i / (num_labels - 1)) * y_range
                y = to_canvas_y(value)
                
                # Dibujar línea de cuadrícula tenue
                if i > 0 and i < num_labels - 1:
                     canvas.create_line(margin + 1, y, canvas_width - margin, y, fill="#dddddd", dash=(2, 2))
                     
                # Etiqueta de texto (redondeada y con separador de miles)
                label_text = formato_float(value)
                canvas.create_text(margin - 5, y, text=label_text, fill="gray", anchor="e")

            # Función de mapeo de datos a coordenadas del canvas (X ya es simple)
            def to_canvas_coords(i, value):
                x = margin + i * x_scale
                y = to_canvas_y(value)
                return x, y
            
            # --- 5. Dibujar Líneas de Referencia (Min/Max/Final) ---
            
            # Función para dibujar una línea de referencia
            def draw_ref_line(y_value, color, label_text, is_final=False):
                y_coord = to_canvas_y(y_value)
                style = (4, 4) if not is_final else (1, 3) # Guiones más cortos para el valor final
                
                # Línea horizontal
                canvas.create_line(margin, y_coord, canvas_width - margin, y_coord, fill=color, dash=style, width=2)
                
                # Etiqueta de texto en el lado derecho
                canvas.create_text(canvas_width - margin + 5, y_coord, 
                                   text=f"{label_text}: {formato_float(y_value)}", fill=color, anchor="w", font=("Segoe UI", 8, "bold"))
                
            # Referencias Almuerzos (Rojo - #e74c3c)
            draw_ref_line(max_lunches, "#e74c3c", "Max. Almuerzos")
            draw_ref_line(min_lunches, "#e74c3c", "Min. Almuerzos")
            draw_ref_line(final_lunches, "#e74c3c", "Final Almuerzos", is_final=True)
            
            # Referencias Costo de Carne (Azul - #3498db)
            draw_ref_line(max_cost, "#3498db", "Max. Carne")
            draw_ref_line(min_cost, "#3498db", "Min. Carne")
            draw_ref_line(final_cost, "#3498db", "Final Carne", is_final=True)


            # --- 6. Plotear Almuerzos Vendidos (Rojo) ---
            points_lunches = []
            for i in range(days):
                x, y = to_canvas_coords(i, lunches_data[i])
                points_lunches.append(x)
                points_lunches.append(y)
                canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="#e74c3c", outline="#c0392b")

            if points_lunches:
                canvas.create_line(points_lunches, fill="#e74c3c", width=2, smooth=True)

            # --- 7. Plotear Costo de Carne (Azul) ---
            points_cost = []
            for i in range(days):
                x, y = to_canvas_coords(i, cost_data[i])
                points_cost.append(x)
                points_cost.append(y)
                canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="#3498db", outline="#2980b9")

            if points_cost:
                canvas.create_line(points_cost, fill="#3498db", width=2, smooth=True)
                
            # --- 8. Leyenda ---
            legend_frame = tk.Frame(plot_frame, bg="white")
            legend_frame.pack(pady=5)
            
            tk.Label(legend_frame, text="● Almuerzos Vendidos (Rojo)", fg="#e74c3c", bg="white", font=("Segoe UI", 10)).pack(side="left", padx=10)
            tk.Label(legend_frame, text="● Costo de Carne (Azul)", fg="#3498db", bg="white", font=("Segoe UI", 10)).pack(side="left", padx=10)

            # --- 9. Estadísticas Clave ---
            stats_frame = tk.LabelFrame(plot_frame, text="Estadísticas de la Simulación",
                                     font=("Segoe UI", 10, "bold"), bg="white", borderwidth=0, relief="flat")
            stats_frame.pack(fill="x", padx=10, pady=10)
            
            # Columna Izquierda: Almuerzos
            left_stats = tk.Frame(stats_frame, bg="white")
            left_stats.pack(side="left", padx=10, pady=5, fill="x", expand=True)
            
            tk.Label(left_stats, text="Almuerzos Vendidos (Rojo)", fg="#e74c3c", bg="white", font=("Segoe UI", 10, "bold")).pack(anchor="w")
            
            tk.Label(left_stats, text=f"   Mínimo: {formato_float(min_lunches)}", bg="white").pack(anchor="w")
            tk.Label(left_stats, text=f"   Máximo: {formato_float(max_lunches)}", bg="white").pack(anchor="w")
            tk.Label(left_stats, text=f"   Promedio: {formato_float(sum(lunches_data)/len(lunches_data))}", bg="white").pack(anchor="w")
            tk.Label(left_stats, text=f"   Valor Final Establecido: {formato_float(final_lunches)}", bg="white", font=("Segoe UI", 10, "bold")).pack(anchor="w")

            # Columna Derecha: Costo de Carne
            right_stats = tk.Frame(stats_frame, bg="white")
            right_stats.pack(side="left", padx=10, pady=5, fill="x", expand=True)

            tk.Label(right_stats, text="Costo de Carne (Azul)", fg="#3498db", bg="white", font=("Segoe UI", 10, "bold")).pack(anchor="w")

            tk.Label(right_stats, text=f"   Mínimo: {formato_float(min_cost)}", bg="white").pack(anchor="w")
            tk.Label(right_stats, text=f"   Máximo: {formato_float(max_cost)}", bg="white").pack(anchor="w")
            tk.Label(right_stats, text=f"   Promedio: {formato_float(sum(cost_data)/len(cost_data))}", bg="white").pack(anchor="w")
            tk.Label(right_stats, text=f"   Valor Final Establecido: {formato_float(final_cost)}", bg="white", font=("Segoe UI", 10, "bold")).pack(anchor="w")

        except Exception as e:
            canvas.create_text(canvas_width / 2, canvas_height / 2, text=f"Error al graficar: {e}", fill="red")
        
    def show_dashboard(self):
        self.clear_main()
        tk.Label(self.main_frame, text="📊 Dashboard", font=("Segoe UI", 26, "bold"),
                  bg="#ecf0f1", fg="#2c3e50").pack(pady=20)

    def show_simulation_view(self):
        self.clear_main()

        tk.Label(self.main_frame, text="🚀 Simulación y Definición de Variables",
                  font=("Segoe UI", 24, "bold"),
                  bg="#ecf0f1", fg="#2c3e50").pack(pady=(20, 8))

        # ===================================
        # CONTENEDOR SCROLLABLE VERTICAL (Lógica Corregida)
        # ===================================
        container = tk.Frame(self.main_frame, bg="#ecf0f1")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        canvas = tk.Canvas(container, bg="#ecf0f1", highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#ecf0f1") # Frame interno que contiene todo

        # 1. Configurar scrollbar y canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 2. El Frame interno notifica al Canvas la altura real (scrollregion)
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # 3. Creamos la ventana dentro del Canvas.
        scroll_window_id = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        # 4. El Canvas notifica al Frame interno el ancho disponible (CORRECCIÓN CLAVE 2)
        # Esto asegura que el scroll_frame use todo el ancho del canvas, forzando la altura si es necesario.
        canvas.bind(
            "<Configure>", 
            lambda e: canvas.itemconfig(scroll_window_id, width=e.width)
        )
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- CONTENEDOR DE DOS COLUMNAS para Entradas ---
        two_column_input_frame = tk.Frame(scroll_frame, bg="#ecf0f1")
        two_column_input_frame.pack(fill="x", padx=20, pady=5)
        
        # CORRECCIÓN CLAVE 3: Aseguramos que las columnas se expandan de manera uniforme
        left_col = tk.Frame(two_column_input_frame, bg="#ecf0f1")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right_col = tk.Frame(two_column_input_frame, bg="#ecf0f1")
        right_col.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # Crear todas las secciones de entrada
        self._create_input_sections(scroll_frame, left_col, right_col)

        # Generar y plotear la gráfica de simulación
        self._generate_and_plot_random_data(scroll_frame)

        # ================================================================
        # BOTÓN GENERAR ESTADOS DE RESULTADOS
        # ================================================================
        button_frame = tk.Frame(scroll_frame, bg="#ecf0f1")
        button_frame.pack(fill="x", padx=20, pady=20)

        tk.Button(
            button_frame,
            text="Generar Estados de Resultados 🧾",
            command=self.show_financial_statements, 
            font=("Segoe UI", 14, "bold"),
            bg="#2ecc71", fg="white",
            activebackground="#27ae60", activeforeground="white",
            bd=0, relief="raised", padx=20, pady=10,
            cursor="hand2"
        ).pack(side="right", padx=10)

    def show_comparison_view(self):
        """
        Limpia el área principal y muestra la interfaz para seleccionar dos reportes
        de estados financieros guardados para su comparación.
        """
        # 1. Limpiar la vista y configurar el título
        self.clear_main()
        
        tk.Label(self.main_frame, text="⚖️ Comparar Estados Financieros", 
                font=("Segoe UI", 24, "bold"), bg="#ecf0f1", fg="#2c3e50").pack(pady=(20, 8))

        # 2. Obtener y Validar Reportes
        reports = get_available_reports()
        
        if not reports or len(reports) < 2:
            tk.Label(self.main_frame, 
                    text="Se necesitan al menos dos simulaciones guardadas para comparar.",
                    font=("Segoe UI", 14), fg="#e74c3c").pack(pady=40)
            tk.Label(self.main_frame, 
                    text=f"Reportes encontrados: {len(reports)}",
                    font=("Segoe UI", 10)).pack()
            return

        # Formatear la lista para mostrarla en el menú (ID - Fecha)
        # r[0] es ReporteID, r[1] es FechaGeneracion
        report_options = [f"ID {r[0]} - {r[1].strftime('%Y-%m-%d %H:%M')}" for r in reports]
        
        # 3. Controles de Selección
        selection_frame = tk.Frame(self.main_frame, bg="#ecf0f1", padx=15, pady=15)
        selection_frame.pack(pady=20)
        
        self.report1_var = tk.StringVar(self.main_frame)
        self.report2_var = tk.StringVar(self.main_frame)
        
        # Establecer valores iniciales
        self.report1_var.set(report_options[0])
        if len(report_options) > 1:
            self.report2_var.set(report_options[1])
        else:
            # En caso de solo dos reportes, igual se seleccionan los dos para inicializar
            self.report2_var.set(report_options[0]) 

        # Selector 1
        tk.Label(selection_frame, text="Reporte Base (1):", font=("Segoe UI", 11), bg="#ecf0f1").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        ttk.Combobox(selection_frame, textvariable=self.report1_var, values=report_options, state="readonly", width=30).grid(row=0, column=1, padx=10, pady=5)

        # Selector 2
        tk.Label(selection_frame, text="Reporte a Comparar (2):", font=("Segoe UI", 11), bg="#ecf0f1").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        ttk.Combobox(selection_frame, textvariable=self.report2_var, values=report_options, state="readonly", width=30).grid(row=1, column=1, padx=10, pady=5)

        # Botón para ejecutar la comparación
        tk.Button(
            self.main_frame, 
            text="Generar Comparación", 
            command=self._execute_comparison_logic, # Llama a la lógica de extracción
            bg="#27ae60", fg="white", font=("Segoe UI", 12, "bold"), relief="raised", padx=10, pady=5
        ).pack(pady=15)

        # Frame donde se mostrará el resultado
        self.comparison_results_frame = tk.Frame(self.main_frame, bg="#ecf0f1")
        self.comparison_results_frame.pack(fill="both", expand=True, padx=20, pady=10)

    def _show_traditional_statement_in_frame(self, target_frame):
        # Lógica de la tabla mantenida

        tk.Label(target_frame, text="🧾 Estado de Resultados Tradicional",
                  font=("Segoe UI", 24, "bold"), bg="#ecf0f1", fg="#2c3e50").pack(pady=(20, 8))

        statement_data = self._calculate_traditional_statement()
        if not statement_data:
            return 
            
        table_frame = tk.LabelFrame(target_frame, text="Resultados Mensuales (Costo de Absorción)",
                                        font=("Segoe UI", 12, "bold"), bg="white", padx=10, pady=10)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        header = tk.Frame(table_frame, bg="#34495e")
        header.pack(fill="x", padx=0, pady=0)
        
        tk.Label(header, text="Concepto", bg="#34495e", fg="white", 
                 font=("Segoe UI", 10, "bold"), width=40, anchor="w").pack(side="left", padx=5, pady=5)
                 
        # 2. Valor ($) (Anchor East, expande y rellena)
        tk.Label(header, text="Valor ($)", bg="#34495e", fg="white", 
                 font=("Segoe UI", 10, "bold"), anchor="e").pack(side="left", padx=5, pady=5, fill="x", expand=True)
                 
        # 3. % (Anchor East, ancho fijo)
        tk.Label(header, text="%", bg="#34495e", fg="white", 
                 font=("Segoe UI", 10, "bold"), width=10, anchor="e").pack(side="left", padx=5, pady=5)
        
        def draw_row(parent, name, value, percentage, bg_color, is_bold=False):
            row = tk.Frame(parent, bg=bg_color)
            row.pack(fill="x")
            font_style = ("Segoe UI", 10, "bold") if is_bold else ("Segoe UI", 10)
        
        # 1. CONCEPTO
        # Mismo ancho fijo que el header
            tk.Label(row, text=name, bg=bg_color, font=font_style, width=40, anchor="w").pack(side="left", padx=5)
        
        # 2. VALOR ($)
        # Usa fill="x" y expand=True para que tome el espacio disponible y empuje el siguiente elemento a la derecha.
            value_str = f"${value:,.2f}"
            tk.Label(row, text=value_str, bg=bg_color, font=font_style, anchor="e").pack(side="left", padx=5, fill="x", expand=True)
        
        # 3. PORCENTAJE (%)
        # Mismo ancho fijo que el header y anchor="e"
            percent_str = f"{percentage*100:,.2f} %"
            tk.Label(row, text=percent_str, bg=bg_color, font=font_style, width=10, anchor="e").pack(side="left", padx=5)
            
        bg_main = "#ecf0f1"
        bg_sub = "white"
        
        # Dibujo de filas (omitido por brevedad, mantenido en el código completo)
        draw_row(table_frame, "VENTAS TOTALES", statement_data["Ventas"][0], statement_data["Ventas"][1], bg_main, True)
        tk.Label(table_frame, text="-- Costos de Ventas (COGS) --", bg=bg_main, font=("Segoe UI", 10, "italic")).pack(fill="x")
        draw_row(table_frame, "  Materia Prima", statement_data["Materia Prima"][0], statement_data["Materia Prima"][1], bg_sub)
        draw_row(table_frame, "  Mano de Obra Directa", statement_data["Mano de Obra Directa"][0], statement_data["Mano de Obra Directa"][1], bg_sub)
        draw_row(table_frame, "  CIF", statement_data["CIF"][0], statement_data["CIF"][1], bg_sub)
        draw_row(table_frame, "TOTAL COSTO DE VENTAS", statement_data["Total Costo de Ventas"][0], statement_data["Total Costo de Ventas"][1], "#bdc3c7", True)
        draw_row(table_frame, "UTILIDAD BRUTA EN VENTAS", statement_data["Utilidad Bruta en Ventas"][0], statement_data["Utilidad Bruta en Ventas"][1], "#2ecc71", True)
        tk.Label(table_frame, text="-- Gastos de Administración y Ventas --", bg=bg_main, font=("Segoe UI", 10, "italic")).pack(fill="x", pady=(5, 0))
        draw_row(table_frame, "  Salario Administración", statement_data["Salario Administración"][0], statement_data["Salario Administración"][1], bg_sub)
        draw_row(table_frame, "  Salario Meseros", statement_data["Salario Meseros"][0], statement_data["Salario Meseros"][1], bg_sub)
        draw_row(table_frame, "  Arrendamiento (Gasto)", statement_data["Arrendamiento (OyV)"][0], statement_data["Arrendamiento (OyV)"][1], bg_sub)
        draw_row(table_frame, "  Depreciación (Gasto)", statement_data["Depreciación (OyV)"][0], statement_data["Depreciación (OyV)"][1], bg_sub)
        draw_row(table_frame, "  Industria y Comercio", statement_data["Industria y Comercio"][0], statement_data["Industria y Comercio"][1], bg_sub)
        draw_row(table_frame, "TOTAL GASTOS ADMÓN. Y VENTAS", statement_data["Total Gastos Admon y Ventas"][0], statement_data["Total Gastos Admon y Ventas"][1], "#bdc3c7", True)
        draw_row(table_frame, "UTILIDAD OPERACIONAL", statement_data["Utilidad Operacional"][0], statement_data["Utilidad Operacional"][1], "#3498db", True)

    def _show_variable_statement_in_frame(self, target_frame):

        tk.Label(target_frame, text="📈 Estado de Resultados por Costo Variable",
                font=("Segoe UI", 24, "bold"), bg="#ecf0f1", fg="#2c3e50").pack(pady=(20, 8))

        statement_data = getattr(self, 'variable_statement_data', None) 
        if not statement_data:
            # Si no se almacenó, intenta calcular por si se llamó fuera del flujo normal
            statement_data = self._calculate_variable_statement()
            if not statement_data:
                return

        table_frame = tk.LabelFrame(
            target_frame,
            text="Resultados Mensuales (Marginal)",
            font=("Segoe UI", 12, "bold"),
            bg="white",
            padx=10,
            pady=10
        )
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        header = tk.Frame(table_frame, bg="#34495e")
        header.pack(fill="x")

        tk.Label(header, text="Concepto", bg="#34495e", fg="white",
                font=("Segoe UI", 10, "bold"), width=40, anchor="w").pack(side="left", padx=5, pady=5)

        tk.Label(header, text="Valor ($)", bg="#34495e", fg="white",
                font=("Segoe UI", 10, "bold"), anchor="e").pack(side="left", padx=5, pady=5, fill="x", expand=True)

        tk.Label(header, text="%", bg="#34495e", fg="white",
                font=("Segoe UI", 10, "bold"), width=10, anchor="e").pack(side="left", padx=5, pady=5)

        def draw_row(parent, name, value, percentage, bg_color, is_bold=False):
            row = tk.Frame(parent, bg=bg_color)
            row.pack(fill="x")

            font_style = ("Segoe UI", 10, "bold") if is_bold else ("Segoe UI", 10)

            tk.Label(row, text=name, bg=bg_color, font=font_style,
                    width=40, anchor="w").pack(side="left", padx=5)

            tk.Label(row, text=f"${value:,.2f}", bg=bg_color, font=font_style,
                    anchor="e").pack(side="left", padx=5, fill="x", expand=True)

            tk.Label(row, text=f"{percentage*100:,.2f} %", bg=bg_color, font=font_style,
                    width=10, anchor="e").pack(side="left", padx=5)

        bg_main = "#ecf0f1"
        bg_sub = "white"
        bg_key = "#f1c40f"

        draw_row(table_frame, "VENTAS TOTALES",
                *statement_data["Ventas"], bg_main, True)

        tk.Label(table_frame, text="-- Costos Variables y Gastos Variables --",
                bg=bg_main, font=("Segoe UI", 10, "italic")).pack(fill="x", pady=(5, 0))

        draw_row(table_frame, "  Materia Prima",
                *statement_data["Costo Variable de Materia Prima"], bg_sub)

        draw_row(table_frame, "  Servicios Públicos (Variable)",
                *statement_data["Costo Variable de Servicios Públicos"], bg_sub)

        draw_row(table_frame, "  Comisiones sobre Ventas",
                *statement_data["Costo Variable de Comisiones"], bg_sub)

        draw_row(table_frame, "  Industria y Comercio (Variable)",
                *statement_data["Costo Variable de Industria y Comercio"], bg_sub)

        draw_row(table_frame, "TOTAL COSTOS Y GASTOS VARIABLES",
                *statement_data["Total Costos Variables"], "#bdc3c7", True)

        # --- MARGEN CONTRIBUCIÓN ---
        draw_row(table_frame, "MARGEN DE CONTRIBUCIÓN",
                *statement_data["Margen de Contribución"], bg_key, True)

        # --- COSTOS FIJOS ---
        tk.Label(table_frame, text="-- Costos y Gastos Fijos --",
                bg=bg_main, font=("Segoe UI", 10, "italic")).pack(fill="x", pady=(5, 0))

        draw_row(table_frame, "  Mano de Obra Fija",
                *statement_data["Costo Fijo de Mano de Obra"], bg_sub)

        draw_row(table_frame, "  Sueldo Administración",
                *statement_data["Sueldo Fijo Administración"], bg_sub)

        draw_row(table_frame, "  Sueldo Meseros",
                *statement_data["Sueldo Fijo Meseros"], bg_sub)

        draw_row(table_frame, "  Arrendamiento",
                *statement_data["Arrendamiento"], bg_sub)

        draw_row(table_frame, "  Depreciación",
                *statement_data["Depreciación"], bg_sub)

        draw_row(table_frame, "TOTAL COSTOS FIJOS",
                *statement_data["Total Costos Fijos"], "#bdc3c7", True)

        # --- UTILIDAD OPERACIONAL ---
        draw_row(table_frame, "UTILIDAD OPERACIONAL",
                *statement_data["Utilidad Operacional"], "#3498db", True)

    def _show_break_even_point_in_frame(self, target_frame):
        """Muestra el cálculo y la gráfica del Punto de Equilibrio usando los datos de _calculate_variable_statement()."""

        pe_data = getattr(self, 'variable_statement_data', None) 
        if not pe_data:
            # Si no se almacenó, intenta calcular por si se llamó fuera del flujo normal
            pe_data = self._calculate_variable_statement()
            if not pe_data:
                return
            
        # ====== Función dibuja filas ======
        def draw_row(parent, name, value, percentage=None, bg_color="white", is_bold=False, currency=True):
            row = tk.Frame(parent, bg=bg_color)
            row.pack(fill="x")
            font_style = ("Segoe UI", 10, "bold") if is_bold else ("Segoe UI", 10)

            tk.Label(row, text=name, bg=bg_color, font=font_style, width=40, anchor="w").pack(side="left", padx=5)

            # Formato valor
            if currency:
                val_str = f"${value:,.2f}"
            else:
                val_str = f"{value:,.0f}"
            
            tk.Label(row, text=val_str, bg=bg_color, font=font_style, anchor="e").pack(side="left", fill="x", expand=True)

            percent_str = ""
            if percentage is not None:
                percent_str = f"({percentage*100:,.2f} %)"

            tk.Label(row, text=percent_str, bg=bg_color, font=font_style, width=12, anchor="e").pack(side="left")

        # ====== Contenedor ======
        main_container = tk.Frame(target_frame, bg="#ecf0f1")
        main_container.pack(fill="both", expand=True, padx=20, pady=10)

        indicators_frame = tk.LabelFrame(
            main_container,
            text="📊 Indicadores del Punto de Equilibrio (Mensual)",
            font=("Segoe UI", 12, "bold"),
            bg="white",
            padx=10,
            pady=10
        )
        indicators_frame.pack(fill="x", padx=10, pady=10)

        bg_pe = "#f39c12"
        bg_obj = "#9b59b6"

        # ====== PUNTOS DE EQUILIBRIO ======
        tk.Label(indicators_frame, text="-- Punto de Equilibrio --",
                bg="white", font=("Segoe UI", 10, "italic")).pack(fill="x", pady=(5, 0))

        draw_row(
            indicators_frame,
            "PE en Unidades (Mensual)",
            pe_data["Punto de Equilibrio (Mes - Unidades)"][0],
            pe_data["Punto de Equilibrio (Mes - Unidades)"][1],
            bg_pe,
            True,
            currency=False
        )

        draw_row(
            indicators_frame,
            "PE en Unidades (Diario)",
            pe_data["Punto de Equilibrio (Día - Unidades)"][0],
            None,
            bg_pe,
            True,
            currency=False
        )

        draw_row(
            indicators_frame,
            "PE en Valor ($)",
            pe_data["Punto de Equilibrio (Valor)"][0],
            pe_data["Punto de Equilibrio (Valor)"][1],
            bg_pe,
            True,
            currency=True
        )

        # ====== MARGEN DE SEGURIDAD ======
        tk.Label(indicators_frame, text="-- Margen de Seguridad --",
                bg="white", font=("Segoe UI", 10, "italic")).pack(fill="x", pady=(5, 0))

        ms_unidades = pe_data["Margen de Seguridad (%)"][0] * self.Entradas["Almuerzos vendidos diariamente"].get() * self.Entradas["Dias trabajados al mes"].get()

        draw_row(indicators_frame, "Margen de Seguridad (%)",
                pe_data["Margen de Seguridad (%)"][0],
                pe_data["Margen de Seguridad (%)"][0],
                "white", False, currency=False)

        draw_row(indicators_frame, "Margen de Seguridad (Valor)",
                pe_data["Margen de Seguridad (Valor)"][0],
                None, "white", False, currency=True)

        # ====== UTILIDAD OBJETIVO ======
        tk.Label(indicators_frame, text="-- Ventas para Utilidad Objetivo (2,500,000) --",
                bg="white", font=("Segoe UI", 10, "italic")).pack(fill="x", pady=(5, 0))

        draw_row(indicators_frame,
                "Ventas Objetivo (Unidades)",
                pe_data["Ventas para Utilidad Objetivo (Unidades)"][0],
                None, bg_obj, False, currency=False)

        draw_row(indicators_frame,
                "Ventas Objetivo (Valor)",
                pe_data["Ventas para Utilidad Objetivo (Valor)"][0],
                None, bg_obj, False, currency=True)

        # =====================================
        #   GRÁFICA PUNTO DE EQUILIBRIO
        # =====================================

        graph_frame = tk.LabelFrame(main_container, text="📉 Gráfica del Punto de Equilibrio",
                                    font=("Segoe UI", 12, "bold"), bg="white",
                                    padx=10, pady=10)
        graph_frame.pack(fill="both", expand=True)

        # ==== Datos ====
        cf = pe_data["Total Costos Fijos"][0]
        u_pe = pe_data["Punto de Equilibrio (Mes - Unidades)"][0]
        valor_pe = pe_data["Punto de Equilibrio (Valor)"][0]
        precio = self.Entradas["Precio del Almuerzo"].get()

        ventas_actuales = self.ventas_totales_mensuales.get()
        unidades_actuales = ventas_actuales / precio if precio else 0

        max_u = int(max(u_pe, unidades_actuales) * 1.3)

        unidades = list(range(0, max_u + 1))
        costo_variable_unitario = pe_data["Total Costos Variables"][0] / unidades_actuales if unidades_actuales else 0

        ingresos = [u * precio for u in unidades]
        costos_totales = [cf + u * costo_variable_unitario for u in unidades]

        fig, ax = plt.subplots(figsize=(7, 5), dpi=100)

        ax.plot(unidades, ingresos, label="Ingresos Totales", linewidth=2)
        ax.plot(unidades, costos_totales, label="Costos Totales", linewidth=2)
        ax.axhline(cf, linestyle="--", label="Costos Fijos")

        ax.plot(u_pe, valor_pe, "o", color="orange", markersize=8, label="Punto de Equilibrio")
        ax.axvline(unidades_actuales, linestyle=":", label="Ventas Actuales")

        ax.set_xlabel("Unidades (almuerzos mensuales)")
        ax.set_ylabel("Valor ($)")
        ax.grid(True, linestyle=":")
        ax.legend()

        canvas = FigureCanvasTkAgg(fig, master=graph_frame)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        canvas.draw()

    def _draw_comparison_table(self, parent_frame, data1, data2, id1, id2, table_key):
        """
        Dibuja una tabla comparativa en un frame, extrayendo datos de un estado específico.
        :param table_key: Clave del diccionario de datos (ej: 'tradicional', 'variable', 'punto_equilibrio').
        """
        # Usar un Frame interior para mantener el Treeview centrado si es necesario
        tree_container = tk.Frame(parent_frame, bg="white")
        # Importante: No usar fill/expand para que el Treeview dentro controle el tamaño
        tree_container.pack(padx=10, pady=10) 

        # 1. Configuración de la Tabla (Treeview)
        tree = ttk.Treeview(tree_container, columns=("R1", "R2", "DIF"), show="headings")
        
        tree.heading("R1", text=f"Base (ID {id1})")
        tree.heading("R2", text=f"Comparar (ID {id2})")
        tree.heading("DIF", text="Diferencia (R2 - R1)")
        
        tree.column("#0", minwidth=250, width=300, anchor="w")
        tree.column("R1", anchor="e", width=180)
        tree.column("R2", anchor="e", width=180)
        tree.column("DIF", anchor="e", width=150)

        # 2. Definición de Conceptos
        conceptos_maestro = {
            "tradicional": [
                ("Ventas Totales", "Ventas", "currency"), ("Materia Prima", "MateriaPrima", "currency"),
                ("Mano de Obra", "ManoDeObra", "currency"), ("CIF (Costo Indirecto)", "CIF", "currency"),
                ("Total Costo Ventas", "TotalCostoVentas", "currency"), ("Utilidad Bruta", "UtilidadBruta", "currency"),
                ("Salario Administración", "SalarioAdministracion", "currency"), 
                ("Total Gastos ADM/Vtas", "TotalGastosAdmonVentas", "currency"),
                ("Utilidad Operacional", "UtilidadOperacional", "currency"),
            ],
            "variable": [
                ("Ventas Totales", "Ventas", "currency"), ("Costo Var. Materia Prima", "CostoVariableMateriaPrima", "currency"),
                ("Total Costos Variables", "TotalCostosVariables", "currency"), ("Margen de Contribución", "MargenContribucion", "currency"),
                ("Costo Fijo Mano Obra", "CostoFijoManoObra", "currency"), ("Sueldo Fijo Administración", "SueldoFijoAdministracion", "currency"),
                ("Total Costos Fijos", "TotalCostosFijos", "currency"), ("Utilidad Operacional", "UtilidadOperacional", "currency"),
                ("Rentabilidad sobre Ventas", "RentabilidadVentas", "percent"),
            ],
            "punto_equilibrio": [
                ("PE en Valor ($)", "PuntoEquilibrioValor", "currency"), ("PE en Unidades (Mes)", "PuntoEquilibrioMesUnidades", "number"),
                ("PE en Unidades (Día)", "PuntoEquilibrioDiaUnidades", "number"), ("Margen de Seguridad (%)", "MargenSeguridadPorc", "percent"),
                ("Ventas Objetivo (Valor)", "VentasUtilidadObjetivoValor", "currency"),
            ],
        }

        conceptos_a_dibujar = conceptos_maestro.get(table_key, [])
        
        # Función auxiliar para formato
        def format_value(value, fmt):
            if value is None: return "N/A"
            try:
                if fmt == "currency":
                    return f"${value:,.2f}"
                elif fmt == "percent":
                    return f"{value*100:,.2f} %"
                elif fmt == "number":
                    return f"{value:,.0f}"
            except (ValueError, TypeError):
                return "N/A"
            return str(value)

        # 3. Llenado de la Tabla
        for name, key, fmt in conceptos_a_dibujar:
            val1 = data1[table_key].get(key) if data1[table_key] else None
            val2 = data2[table_key].get(key) if data2[table_key] else None
            
            diff = "N/A"
            is_numeric = isinstance(val1, (int, float)) and isinstance(val2, (int, float))
            
            if is_numeric:
                diff = val2 - val1
            
            r1_fmt = format_value(val1, fmt)
            r2_fmt = format_value(val2, fmt)
            
            diff_fmt = "N/A"
            
            if is_numeric:
                diff = float(diff) # Aseguramos que 'diff' es flotante
                
                if fmt == "currency":
                    # Formato corregido: + para el signo, , para miles, .2f para decimales
                    diff_fmt = f"${diff:+,.2f}" 
                elif fmt == "percent":
                    diff_fmt = f"{diff*100:+,.2f} %"
                else: # 'number'
                    diff_fmt = f"{diff:+,.0f}"
                    
            # Resaltado
            bg_color = 'white'
            if is_numeric and abs(diff) > 0.001 and val1 is not None:
                bg_color = '#d4e6f1'
                
            tree.insert("", "end", text=name, values=(r1_fmt, r2_fmt, diff_fmt), tags=(bg_color,))
            tree.tag_configure(bg_color, background=bg_color)
            
        # Añadir barra de desplazamiento
        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=tree.yview)
        
        # 🚨 Empaquetado corregido: Treeview y Scrollbar
        vsb.pack(side='right', fill='y')
        # Importante: Quitamos expand=True del tree.pack()
        tree.pack(side="left", fill="both") 
        
        tree.configure(yscrollcommand=vsb.set)

    def _extract_break_even_data(self, all_data):
        """
        Extrae solo los datos de Punto de Equilibrio del diccionario completo.
        """
        pe_keys = [
            "Punto de Equilibrio (Mes - Unidades)",
            "Punto de Equilibrio (Día - Unidades)",
            "Punto de Equilibrio (Valor)",
            "Margen de Seguridad (%)",
            "Margen de Seguridad (Valor)",
            "Ventas para Utilidad Objetivo (Unidades)",
            "Ventas para Utilidad Objetivo (Valor)",
        ]
        
        # Filtrar solo las claves de PE
        datos_pe = {k: all_data[k] for k in pe_keys if k in all_data}
        return datos_pe 

    def _extract_variable_statement_data(self, all_data):
        """
        Extrae solo los datos del Estado Variable (excluyendo PE).
        """
        # Identificar claves de PE para excluirlas
        pe_keys = [
            "Punto de Equilibrio (Mes - Unidades)",
            "Punto de Equilibrio (Día - Unidades)",
            "Punto de Equilibrio (Valor)",
            "Margen de Seguridad (%)",
            "Margen de Seguridad (Valor)",
            "Ventas para Utilidad Objetivo (Unidades)",
            "Ventas para Utilidad Objetivo (Valor)",
        ]
        
        # Crear un nuevo diccionario excluyendo las claves de PE
        datos_variable = {k: v for k, v in all_data.items() if k not in pe_keys}
        return datos_variable

    def _exportar_pdf(self):
        # Asegúrate de importar 'os' en la parte superior de tu archivo Proyecto.py si aún no lo has hecho.
        # ----------------------------------------------------
        # PASO 1: Determinar la ruta a la carpeta de Descargas
        # ----------------------------------------------------
        
        # El directorio 'Home' del usuario (Ej: C:\Users\wilme)
        user_home = os.path.expanduser("~") 
        
        # Construye la ruta completa a la carpeta de Descargas
        # Esto funciona para la mayoría de sistemas, incluyendo Windows.
        descargas_path = os.path.join(user_home, "Downloads")

        # Define el nombre del archivo final
        nombre_archivo_pdf = "Reporte_Financiero_Simulacion.pdf"
        
        # Combina la ruta de descargas con el nombre del archivo
        ruta_final_pdf = os.path.join(descargas_path, nombre_archivo_pdf)
        # ----------------------------------------------------

        # Obtener datos y generar figura (asumiendo que ya has implementado las correcciones previas)
        datos_completos = self._calculate_variable_statement()
        datos_variable = self._extract_variable_statement_data(datos_completos)
        datos_tradicional = self._calculate_traditional_statement()
        datos_pe = self._extract_break_even_data(datos_completos)
        fig_pe = self._generate_break_even_figure()

        # Llamar a la función del archivo externo usando la nueva ruta
        exportar_simulacion_pdf(
            ruta_final_pdf, # Usar la ruta completa a Descargas
            datos_variable,
            datos_tradicional,
            datos_pe,
            fig_pe
        )

        messagebox.showinfo("PDF generado", f"El reporte fue exportado correctamente en:\n{ruta_final_pdf}")

    def _generate_break_even_figure(self):
        """
        Devuelve un matplotlib Figure del punto de equilibrio.
        """
        import matplotlib.pyplot as plt

        # pe_data contiene todos los resultados de _calculate_variable_statement
        pe_data = self._calculate_variable_statement() 
        fig, ax = plt.subplots(figsize=(7, 5), dpi=100)

        # 1. Obtener Costos Fijos (Existe como clave directa)
        cf = pe_data["Total Costos Fijos"][0]
        
        # 2. Obtener Precio Unitario (Se debe obtener directamente del input o calcular el costo unitario)
        # Se obtiene el precio unitario del input de la aplicación
        p = self.Entradas["Precio del Almuerzo"].get() 
        
        # 3. Obtener Costo Variable Unitario (No existe, debemos recalcularlo o calcularlo primero en _calculate_variable_statement)
        # Una forma rápida es usar el Total Costos Variables y las unidades totales:
        total_costos_variables = pe_data["Total Costos Variables"][0]
        almuerzos_mensuales = self.Entradas["Almuerzos vendidos diariamente"].get() * self.Entradas["Dias trabajados al mes"].get()
        cvu = total_costos_variables / almuerzos_mensuales if almuerzos_mensuales else 0

        # 4. Punto de Equilibrio en Unidades (Existe como clave con índice [0])
        pe_u = pe_data["Punto de Equilibrio (Mes - Unidades)"][0]
        
        # 5. Ventas Actuales en Unidades (No existe como clave, se calcula con los inputs)
        ventas_actuales_u = almuerzos_mensuales

        # ---------------------------------------------------------------------
        # El resto del código usa las variables locales (p, cf, cvu, pe_u, ventas_actuales_u) 
        # que ahora sí están definidas correctamente.
        # ---------------------------------------------------------------------
        max_u = max(ventas_actuales_u, pe_u) * 1.3
        unidades = range(0, int(max_u) + 1, max(1, int(max_u // 10)))

        ingresos = [u * p for u in unidades]
        costos_totales = [cf + u * cvu for u in unidades]

        ax.plot(unidades, ingresos, label="Ingresos Totales", color='#2ecc71', linewidth=2)
        ax.plot(unidades, costos_totales, label="Costos Totales", color='#e74c3c', linewidth=2)
        ax.axhline(cf, color='#34495e', linestyle='--', label="Costos Fijos")
        
        # Corregir la obtención del valor del PE
        pe_valor = pe_data["Punto de Equilibrio (Valor)"][0]
        ax.plot(pe_u, pe_valor, 'o', color='#f39c12', markersize=8, label='Punto de Equilibrio')
        
        ax.axvline(ventas_actuales_u, color='#3498db', linestyle=':', label="Ventas Actuales (Uds)")
        
        # ... (resto de la configuración de la gráfica)
        # ...
        
        return fig

    def show_financial_statements(self):
        """
        Función maestra que limpia el área principal y muestra los dos estados
        de resultados y el punto de equilibrio en una interfaz de pestañas.
        """
        self.clear_main()

        self.variable_statement_data = self._calculate_variable_statement() 
        self.break_even_data = self._extract_break_even_data(self.variable_statement_data)
        # ---------------------------------------
        # 🔹 Título principal
        # ---------------------------------------
        tk.Label(
            self.main_frame,
            text="🧾 Análisis Financiero de Costeo y PE",
            font=("Segoe UI", 24, "bold"),
            bg="#ecf0f1", fg="#2c3e50"
        ).pack(pady=(20, 8))

        # ---------------------------------------
        # 🔹 Barra de herramientas superior (BOTÓN)
        # ---------------------------------------
        toolbar = tk.Frame(self.main_frame, bg="#ecf0f1")
        toolbar.pack(fill="x", padx=20)

        btn_exportar = tk.Button(
            toolbar,
            text="📥 Descargar Reporte PDF",
            font=("Segoe UI", 11, "bold"),
            bg="#3498db",
            fg="white",
            relief="raised",
            padx=10,
            pady=5,
            command=self._exportar_pdf 
        )
        btn_exportar.pack(side="right", padx=5, pady=5)

        # ---------------------------------------
        # 🔹 Contenedor Notebook
        # ---------------------------------------
        notebook = ttk.Notebook(self.main_frame)
        notebook.pack(fill="both", expand=True, padx=20, pady=10)

        traditional_frame = tk.Frame(notebook, bg="#ecf0f1")
        variable_frame = tk.Frame(notebook, bg="#ecf0f1")
        break_even_frame = tk.Frame(notebook, bg="#ecf0f1")

        notebook.add(traditional_frame, text="Costo Tradicional")
        notebook.add(variable_frame, text="Costo Variable")
        notebook.add(break_even_frame, text="Punto de Equilibrio 📊")

        # Poblar frames
        self._show_traditional_statement_in_frame(traditional_frame)
        # Pasar los datos al método de visualización o dejar que acceda a self.
        self._show_variable_statement_in_frame(variable_frame) 
        self._show_break_even_point_in_frame(break_even_frame)

        messagebox.showinfo("Información",
            "Reportes Guardados en la bd correctamente.\n\n"
        )

        notebook.select(0)


if __name__ == "__main__":
    # Nota: Asegúrate de que el archivo 'Generacion_Variables.py' esté en la misma carpeta 
    # y contenga la función 'generate_simulation_data'.
    root = tk.Tk()
    app = ModernFinancialUI(root)
    root.mainloop()