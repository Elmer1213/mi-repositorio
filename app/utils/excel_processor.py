import pandas as pd
from typing import List, Dict, Tuple
from fastapi import UploadFile
import io
from app.schemas import ExcelPreviewRow


class ExcelProcessor:
    
    REQUIRED_COLUMNS = ['name', 'email']
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    
    @staticmethod
    async def validate_file_size(file: UploadFile) -> bool:
        """Valida que el archivo no exceda el tamaño máximo"""
        contents = await file.read()
        await file.seek(0)  # Regresa al inicio del archivo
        return len(contents) <= ExcelProcessor.MAX_FILE_SIZE
    
    @staticmethod
    async def read_excel(file: UploadFile) -> pd.DataFrame:
        """Lee el archivo Excel y retorna un DataFrame"""
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents), engine='openpyxl')
        
        # Limpiar nombres de columnas (quitar espacios)
        df.columns = df.columns.str.strip().str.lower()
        
        return df
    
    @staticmethod
    def validate_structure(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Valida que el Excel tenga las columnas requeridas"""
        errors = []
        columns = df.columns.tolist()
        
        for col in ExcelProcessor.REQUIRED_COLUMNS:
            if col not in columns:
                errors.append(f"Falta la columna requerida: '{col}'")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_row(row: Dict, row_number: int) -> ExcelPreviewRow:
        """Valida una fila individual"""
        errors = []
        
        # Validar que name no esté vacío
        if pd.isna(row.get('name')) or str(row.get('name')).strip() == '':
            errors.append("El campo 'name' es obligatorio")
        
        # Validar que email no esté vacío y tenga formato válido
        email = row.get('email')
        if pd.isna(email) or str(email).strip() == '':
            errors.append("El campo 'email' es obligatorio")
        elif '@' not in str(email):
            errors.append("El email no tiene un formato válido")
        
        return ExcelPreviewRow(
            row_number=row_number,
            name=str(row.get('name', '')).strip(),
            email=str(row.get('email', '')).strip(),
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    @staticmethod
    def get_preview(df: pd.DataFrame, max_rows: int = 50) -> List[ExcelPreviewRow]:
        """Obtiene un preview de las primeras filas con validación"""
        preview = []
        
        for idx, row in df.head(max_rows).iterrows():
            validated_row = ExcelProcessor.validate_row(row.to_dict(), idx + 2)  # +2 porque Excel empieza en 1 y tiene headers
            preview.append(validated_row)
        
        return preview
    
    @staticmethod
    async def get_sheet_names(file: UploadFile) -> List[str]:
        """Obtiene los nombres de las hojas del Excel"""
        contents = await file.read()
        await file.seek(0)
        excel_file = pd.ExcelFile(io.BytesIO(contents))
        return excel_file.sheet_names