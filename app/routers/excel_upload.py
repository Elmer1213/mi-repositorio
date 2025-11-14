from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import pandas as pd
import asyncio
from datetime import datetime


from app.database import get_db
from app.models import User, ExcelUploadLog, UploadStatusEnum
from app.schemas import ExcelPreviewResponse, UploadLogResponse, UploadProgressResponse
from app.utils.excel_processor import ExcelProcessor
from app.utils.logger_config import logger

router = APIRouter(prefix="/api/excel", tags=["Excel Upload"])


@router.post("/validate-file")
async def validate_excel_file(file: UploadFile = File(...)):
    """
    Valida el tamaño y formato del archivo Excel
    """
    # Validar extensión
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe ser formato Excel (.xlsx o .xls)"
        )
    
    # Validar tamaño
    is_valid_size = await ExcelProcessor.validate_file_size(file)
    if not is_valid_size:
        raise HTTPException(
            status_code=400,
            detail=f"El archivo excede el tamaño máximo permitido de 10 MB"
        )
    
    return {
        "message": "Archivo válido",
        "filename": file.filename,
        "size_ok": is_valid_size
    }


@router.get("/sheets")
async def get_excel_sheets(file: UploadFile = File(...)):
    """
    Obtiene los nombres de las hojas del archivo Excel
    """
    try:
        sheet_names = await ExcelProcessor.get_sheet_names(file)
        return {
            "sheets": sheet_names,
            "total": len(sheet_names)
        }
    except Exception as e:
        logger.error(f"Error al leer hojas de Excel: {str(e)}")
        raise HTTPException(status_code=400, detail="Error al leer el archivo Excel")


@router.post("/preview", response_model=ExcelPreviewResponse)
async def preview_excel_data(file: UploadFile = File(...)):
    """
    Muestra un preview de los datos del Excel con validaciones
    """
    try:
        # Leer Excel
        df = await ExcelProcessor.read_excel(file)
        
        # Validar estructura
        is_valid, errors = ExcelProcessor.validate_structure(df)
        if not is_valid:
            raise HTTPException(status_code=400, detail={"errors": errors})
        
        # Obtener preview con validaciones
        preview_rows = ExcelProcessor.get_preview(df, max_rows=50)
        
        has_errors = any(not row.is_valid for row in preview_rows)
        
        return ExcelPreviewResponse(
            total_rows=len(df),
            preview_rows=preview_rows,
            columns=df.columns.tolist(),
            has_errors=has_errors
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al procesar preview: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al procesar el archivo")


@router.post("/upload")
async def upload_excel_data(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Carga los datos del Excel a la base de datos
    """
    try:
        # Leer y validar Excel
        df = await ExcelProcessor.read_excel(file)
        is_valid, errors = ExcelProcessor.validate_structure(df)
        
        if not is_valid:
            raise HTTPException(status_code=400, detail={"errors": errors})
        
        # Crear log de carga
        upload_log = ExcelUploadLog(
            filename=file.filename,
            status=UploadStatusEnum.PROCESSING,
            total_rows=len(df)
        )
        db.add(upload_log)
        db.commit()
        db.refresh(upload_log)
        
        # Procesar en background
        background_tasks.add_task(
            process_excel_data,
            df=df,
            upload_log_id=upload_log.id,
            db=db
        )
        
        return {
            "message": "Carga iniciada",
            "upload_id": upload_log.id,
            "total_rows": len(df)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al iniciar carga: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al procesar el archivo")


# ============================================
# NUEVO ENDPOINT: ESTADÍSTICAS
# ============================================
@router.get("/stats")
async def get_upload_stats(db: Session = Depends(get_db)):
    """
    Obtiene estadísticas de las cargas de Excel
    
    Returns:
        - total_uploads: Número total de cargas
        - total_successful: Total de filas exitosas
        - total_failed: Total de filas fallidas
        - chart_data: Datos para gráficos (últimas 10 cargas)
    """
    try:
        logger.info("📊 Obteniendo estadísticas de cargas...")
        
        # Estadísticas totales
        total_uploads = db.query(func.count(ExcelUploadLog.id)).scalar() or 0
        total_successful = db.query(func.sum(ExcelUploadLog.successful_rows)).scalar() or 0
        total_failed = db.query(func.sum(ExcelUploadLog.failed_rows)).scalar() or 0
        
        logger.info(f"Total uploads: {total_uploads}, Exitosas: {total_successful}, Fallidas: {total_failed}")
        
        # Últimas 10 cargas para los gráficos
        recent_uploads = (
            db.query(ExcelUploadLog)
            .order_by(ExcelUploadLog.uploaded_at.desc())
            .limit(10)
            .all()
        )
        
        # Construir datos para gráficos
        chart_data = {
            'labels': [],
            'successful': [],
            'failed': [],
            'dates': []
        }
        
        # Invertir para orden cronológico (más antiguo al más nuevo)
        for upload in reversed(recent_uploads):
            # Usar filename o un identificador
            label = upload.filename if upload.filename else f'Carga #{upload.id}'
            chart_data['labels'].append(label)
            chart_data['successful'].append(upload.successful_rows or 0)
            chart_data['failed'].append(upload.failed_rows or 0)
            
            # Formatear fecha (usa uploaded_at según tu modelo)
            if upload.uploaded_at:
                date_str = upload.uploaded_at.strftime('%Y-%m-%d')
            else:
                date_str = datetime.now().strftime('%Y-%m-%d')
            chart_data['dates'].append(date_str)
        
        logger.info(f"📊 Datos de gráficos: {len(chart_data['labels'])} cargas")
        
        response = {
            'total_uploads': int(total_uploads),
            'total_successful': int(total_successful) if total_successful else 0,
            'total_failed': int(total_failed) if total_failed else 0,
            'chart_data': chart_data
        }
        
        logger.info(f"✅ Estadísticas obtenidas exitosamente")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error al obtener estadísticas: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener estadísticas: {str(e)}"
        )
# ============================================


@router.get("/logs", response_model=List[UploadLogResponse])
async def get_upload_logs(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Obtiene el historial de cargas
    """
    logs = db.query(ExcelUploadLog).order_by(ExcelUploadLog.uploaded_at.desc()).limit(limit).all()
    return logs


@router.get("/logs/{upload_id}", response_model=UploadLogResponse)
async def get_upload_log(upload_id: int, db: Session = Depends(get_db)):
    """
    Obtiene el detalle de una carga específica
    """
    log = db.query(ExcelUploadLog).filter(ExcelUploadLog.id == upload_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log no encontrado")
    return log


def process_excel_data(df: pd.DataFrame, upload_log_id: int, db: Session):
    """
    Procesa los datos del Excel e inserta en la base de datos
    Esta función se ejecuta en background
    """
    successful = 0
    failed = 0
    
    try:
        for idx, row in df.iterrows():
            try:
                # Validar fila
                validated_row = ExcelProcessor.validate_row(row.to_dict(), idx + 2)
                
                if not validated_row.is_valid:
                    failed += 1
                    continue
                
                # Verificar si el email ya existe
                existing_user = db.query(User).filter(User.email == validated_row.email).first()
                if existing_user:
                    failed += 1
                    continue
                
                # Crear nuevo usuario
                new_user = User(
                    name=validated_row.name,
                    email=validated_row.email
                )
                db.add(new_user)
                db.commit()
                successful += 1
                
            except Exception as e:
                logger.error(f"Error al procesar fila {idx + 2}: {str(e)}")
                failed += 1
                db.rollback()
        
        # Actualizar log
        upload_log = db.query(ExcelUploadLog).filter(ExcelUploadLog.id == upload_log_id).first()
        if upload_log:
            upload_log.status = UploadStatusEnum.COMPLETED
            upload_log.successful_rows = successful
            upload_log.failed_rows = failed
            db.commit()
        
        logger.info(f"Carga completada: {successful} exitosos, {failed} fallidos")
    
    except Exception as e:
        logger.error(f"Error crítico en carga: {str(e)}")
        upload_log = db.query(ExcelUploadLog).filter(ExcelUploadLog.id == upload_log_id).first()
        if upload_log:
            upload_log.status = UploadStatusEnum.FAILED
            upload_log.error_message = str(e)
            db.commit()


async def process_excel_data_with_progress(
    df: pd.DataFrame, 
    upload_log_id: int, 
    db: Session,
    websocket_manager
):
    """
    Procesa los datos del Excel e inserta en la base de datos
    Envía progreso vía WebSocket
    """
    successful = 0
    failed = 0
    total = len(df)
    
    try:
        for idx, row in df.iterrows():
            try:
                # Validar fila
                validated_row = ExcelProcessor.validate_row(row.to_dict(), idx + 2)
                
                if not validated_row.is_valid:
                    failed += 1
                    continue
                
                # Verificar si el email ya existe
                existing_user = db.query(User).filter(User.email == validated_row.email).first()
                if existing_user:
                    failed += 1
                    continue
                
                # Crear nuevo usuario
                new_user = User(
                    name=validated_row.name,
                    email=validated_row.email
                )
                db.add(new_user)
                db.commit()
                successful += 1
                
                # Enviar progreso vía WebSocket
                current = idx + 1
                percentage = (current / total) * 100
                await websocket_manager.send_progress({
                    "current": current,
                    "total": total,
                    "percentage": round(percentage, 2),
                    "successful": successful,
                    "failed": failed,
                    "status": "processing"
                })
                
                # Pequeña pausa para simular procesamiento (opcional)
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error al procesar fila {idx + 2}: {str(e)}")
                failed += 1
                db.rollback()
        
        # Actualizar log
        upload_log = db.query(ExcelUploadLog).filter(ExcelUploadLog.id == upload_log_id).first()
        if upload_log:
            upload_log.status = UploadStatusEnum.COMPLETED
            upload_log.successful_rows = successful
            upload_log.failed_rows = failed
            db.commit()
        
        # Enviar progreso final
        await websocket_manager.send_progress({
            "current": total,
            "total": total,
            "percentage": 100,
            "successful": successful,
            "failed": failed,
            "status": "completed"
        })
        
        logger.info(f"Carga completada: {successful} exitosos, {failed} fallidos")
    
    except Exception as e:
        logger.error(f"Error crítico en carga: {str(e)}")
        upload_log = db.query(ExcelUploadLog).filter(ExcelUploadLog.id == upload_log_id).first()
        if upload_log:
            upload_log.status = UploadStatusEnum.FAILED
            upload_log.error_message = str(e)
            db.commit()
        
        await websocket_manager.send_progress({
            "status": "failed",
            "error": str(e)
        })