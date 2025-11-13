"""
Script para convertir archivos CSV a Excel (.xlsx)
Uso: python convertir_csv_a_excel.py
"""

import pandas as pd
import os

# Lista de archivos CSV a convertir
csv_files = [
    'test_usuarios_validos.csv',
    'test_usuarios_con_errores.csv',
    'test_usuarios_grande.csv',
    'plantilla_usuarios.csv',
    'test_usuarios_duplicados.csv'
]

def convert_csv_to_excel(csv_file):
    """
    Convierte un archivo CSV a Excel
    """
    try:
        # Leer CSV
        df = pd.read_csv(csv_file)
        
        # Nombre del archivo Excel
        excel_file = csv_file.replace('.csv', '.xlsx')
        
        # Guardar como Excel
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        print(f"Convertido: {csv_file} → {excel_file}")
        return True
    
    except Exception as e:
        print(f"Error al convertir {csv_file}: {str(e)}")
        return False


def create_multi_sheet_excel():
    """
    Crea un archivo Excel con múltiples hojas (para probar selector)
    """
    try:
        with pd.ExcelWriter('test_usuarios_multihoja.xlsx', engine='openpyxl') as writer:
            # Hoja 1: Estudiantes
            df1 = pd.DataFrame({
                'name': ['Juan Pérez', 'María González', 'Carlos López'],
                'email': ['juan@sena.edu.co', 'maria@sena.edu.co', 'carlos@sena.edu.co']
            })
            df1.to_excel(writer, sheet_name='Estudiantes', index=False)
            
            # Hoja 2: Instructores
            df2 = pd.DataFrame({
                'name': ['Ana Martínez', 'Luis Torres', 'Diana Ramírez'],
                'email': ['ana.instructor@sena.edu.co', 'luis.instructor@sena.edu.co', 'diana.instructor@sena.edu.co']
            })
            df2.to_excel(writer, sheet_name='Instructores', index=False)
            
            # Hoja 3: Administrativos
            df3 = pd.DataFrame({
                'name': ['Jorge Hernández', 'Paula Díaz'],
                'email': ['jorge.admin@sena.edu.co', 'paula.admin@sena.edu.co']
            })
            df3.to_excel(writer, sheet_name='Administrativos', index=False)
        
        print("Archivo multi-hoja creado: test_usuarios_multihoja.xlsx")
        return True
    
    except Exception as e:
        print(f"Error al crear archivo multi-hoja: {str(e)}")
        return False


def main():
    print("=" * 60)
    print("Convirtiendo archivos CSV a Excel")
    print("=" * 60)
    
    success_count = 0
    
    # Convertir archivos CSV
    for csv_file in csv_files:
        if os.path.exists(csv_file):
            if convert_csv_to_excel(csv_file):
                success_count += 1
        else:
            print(f"Archivo no encontrado: {csv_file}")
    
    # Crear archivo multi-hoja
    if create_multi_sheet_excel():
        success_count += 1
    
    print("=" * 60)
    print(f"Completado: {success_count} archivos Excel creados")
    print("=" * 60)


if __name__ == "__main__":
    # Verificar que pandas y openpyxl estén instalados
    try:
        import pandas
        import openpyxl
    except ImportError:
        print("Error: Instala las dependencias primero:")
        print("pip install pandas openpyxl")
        exit(1)
    
    main()