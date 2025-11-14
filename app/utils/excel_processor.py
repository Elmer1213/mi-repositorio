import pandas as pd
from typing import List, Dict, Tuple, Any
from fastapi import UploadFile
import io
from app.schemas import ExcelPreviewRow
import re
from app.utils.logger_config import logger


class ExcelProcessor:
    
    """Clase para procesar y validar archivos Excel"""
    
    REQUIRED_COLUMNS = ['name', 'email']
    
    # 10 MB
    MAX_FILE_SIZE = 10 * 1024 * 1024  
    
    @staticmethod
    async def validate_file_size(file: UploadFile) -> bool:
        
        """Valida que el archivo no exceda el tamaño máximo"""
        try:
            contents = await file.read()
            # Regresa al inicio del archivo
            await file.seek(0)  
            return len(contents) <= ExcelProcessor.MAX_FILE_SIZE
        except Exception as e:
            logger.error(f"Error validando tamaño: {str(e)}")
            return False
        
    @staticmethod
    async def get_sheet_names(file: UploadFile) -> List[str]:
        
        """Obtiene los nombres de las hojas del Excel"""
        try:
            contents = await file.read()
            await file.seek(0)
            
             # Leer con pandas
            excel_file = pd.ExcelFile((contents))
            return excel_file.sheet_names
        except Exception as e:
            logger.error(f"Error leyendo hojas: {str(e)}")
            raise
    
    
    @staticmethod
    async def read_excel(file: UploadFile, sheet_name: str = None) -> pd.DataFrame:
        
        """Lee el archivo Excel y retorna un DataFrame"""
        
        try:
            contents = await file.read()
            await file.seek(0)
            
            #Leer el excel
            df = pd.read_excel(contents, sheet_name=sheet_name or 0)
        
            # Limpiar nombres de columnas (quitar espacios)
            df.columns = df.columns.str.strip().str.lower()
            
            #Eliminar filas completamente vacias
            df = df.dropna(how='all')
            
            return df
        
        except Exception as e:
            logger.error(f"Error leyendo el Excel: {str(e)}")
            raise
    
    @staticmethod
    def validate_structure(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        
        """Valida que el Excel tenga las columnas requeridas"""
        
        errors = []
        
        #Validar que existan las columnas requeridas
        missing_columns = [col for col in ExcelProcessor.REQUIRED_COLUMNS if col not in df.columns]
        
        if missing_columns:
            errors.append(f"Columnas faltantes: {', '.join(missing_columns)}")
        
        # Validar que no esté vacío
        if len(df) == 0:
            errors.append("El archivo está vacío")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_email(email: str) -> bool:
        
        """Valida que el formato de email usando regex"""
        
        if pd.isna(email) or not isinstance(email, str):
            return False
        
        #expresion regular
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$' 
        return bool(re.match(pattern, email.strip()))
    
    @staticmethod
    def validate_name(name: str) -> bool:
        
        """Valida que el nombre no esté vacío y tenga formato válido"""
        
        if pd.isna(name) or not isinstance(name, str):
            return False
        
        name = name.strip()
        
        #Nombre debe tenwr al menos 2 caracteres
        if len(name) < 2:
            return False
        
        #Nombre no debe tcontener solo numeros
        if name.isdigit():
            return False
        
        return True
    
    @staticmethod
    def validate_row(row: Dict[str, Any], row_number: int) -> ExcelPreviewRow:
        
        """Valida una fila individual y devuelve un ExcelPreviewRow"""
        
        errors = []
        
        #Obterne los valores
        name = row.get('name', '')
        email = row.get('email', '')
        
        if not ExcelProcessor.validate_name(name):
            errors.append("Email invalido")
        
        #Limpiar valores
        clean_name = str(name).strip() if pd.notna(name) else ""
        clean_email = str(email).strip().lower() if pd.notna(email) else ""
        
        return ExcelPreviewRow(
            row_number=row_number,
            name=clean_name,
            email=clean_email,
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    @staticmethod
    def get_preview(df: pd.DataFrame, max_rows: int = 50) -> List[ExcelPreviewRow]:
        
        """Obtiene un preview de las primeras filas con validación"""
        
        preview_rows = []
        
        for idx, row in df.head(max_rows).iterrows():
            validated_row = ExcelProcessor.validate_row(
                row.to_dict(),
                # +2 porque Excel empieza en 1 y hay header
                idx + 2 
            )
            preview_rows.append(validated_row)
            
        return preview_rows
    
    @staticmethod
    def get_validation_summary(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Devuelve un resumen de validación del archivo completo
        """
        total_rows = len(df)
        valid_rows = 0
        invalid_rows = 0
        
        for idx, row in df.iterrows():
            validated = ExcelProcessor.validate_row(row.to_dict(), idx + 2)
            if validated.is_valid:
                valid_rows += 1
            else:
                invalid_rows += 1
        
        return {
            "total_rows": total_rows,
            "valid_rows": valid_rows,
            "invalid_rows": invalid_rows,
            "success_rate": (valid_rows / total_rows * 100) if total_rows > 0 else 0
        }
    