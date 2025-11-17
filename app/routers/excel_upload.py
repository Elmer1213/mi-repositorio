from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
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
    
    try:
        # Validar que el archivo existe
        if not file or not file.filename:
            raise HTTPException(
                status_code=400,
                detail="No se proporcionó ningún archivo"
            )
            
        #Validar extensión
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="El archivo debe ser formato Excel (.xlsx o .xls)"
        )
    
        # Validar tamaño
        try:
            is_valid_size = await ExcelProcessor.validate_file_size(file)
        except Exception as e:
            logger.error(f"Error al validar tamaño del archivo: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Error al validar el tamaño del archivo"
            )
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inesperado en validación de archivo: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Erro inseperado al validar el archivo"
        )


@router.get("/sheets")
async def get_excel_sheets(file: UploadFile = File(...)):
    """
    Obtiene los nombres de las hojas del archivo Excel
    """
    try:
        if not file or not file.filename:
            raise HTTPException(
                status_code=400,
                detail="No se proporciona ningun archivo"
            )
            
        sheet_names = await ExcelProcessor.get_sheet_names(file)
        
        if not sheet_names or len(sheet_names) == 0:
            raise HTTPException(
                status_code=400,
                detail="El archivo Excel no contiene hojas validas"
            )
            
        return {
            "sheets": sheet_names,
            "total": len(sheet_names)
        }
    except Exception as e:
        raise
    except Exception as e:
        logger.error(f"Error al leer hojas de Excel: {str(e)}")
        raise HTTPException(
            status_code=400, 
            detail="Error al leer el archivo Excel"
        )


@router.post("/preview", response_model=ExcelPreviewResponse)
async def preview_excel_data(file: UploadFile = File(...)):
    """
    Muestra un preview de los datos del Excel con validaciones
    """
    
    try:
        if not file or not file.filename:
            raise HTTPException(
                status_code=400,
                detail="No se proporcionó ningun archivo"
            )

        #Leer Excel
        try:
            df = await ExcelProcessor.read_excel(file)
        except Exception as e:
            logger.error(f"Error al leer Excel: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail="No se puede leer el archivo Excel. Verificar que no este corrupto."
            )
            
        if df is None or df.empty:
            raise HTTPException(
                status_code=400,
                detail="El archivo Excel esta vacio o no contiene datos validos"
            )
            
            
        # Validar estructura
        try:
            is_valid, errors = ExcelProcessor.validate_structure(df)
        except Exception as e:
            logger.error(f"Error al validar estructura: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail="Error al validar la estructura del el archhivo"
            )
            
        if not is_valid:
            if errors:
                raise HTTPException(status_code=400, detail={"errors": errors})
            else:
                raise HTTPException(
                    status_code=400,
                    detail="La estructura del archivo no es valida"
                )
        
        
        # Obtener preview con validaciones
        try:
            preview_rows = ExcelProcessor.get_preview(df, max_rows=50)
        except Exception as e:
            logger.error(f"Error al generar preview: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Erro al generar la vista previa"
            )
        
        has_errors = any(not row.is_valid for row in preview_rows) if preview_rows else False
        
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
        raise HTTPException(
            status_code=500, 
            detail="Error al procesar el archivo"
        )


@router.post("/upload")
async def upload_excel_data(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Carga los datos del Excel a la base de datos
    """
    upload_log = None
    try:
        if not file or not file.filename:
            raise HTTPException(
                status_code=400,
                detail="No se proporcionó ningun archivo"
            )
        # Leer y validar Excel
        try:
            df = await ExcelProcessor.read_excel(file)
        except Exception as e:
            logger.error(f"Error al leer Excel: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail="No se puede leer el archivo Excel"
            )
            
        if df is None or df.empty:
            raise HTTPException(
                status_code=400,
                detail="El archivo Excel esta vacío"
            )
            
        try:
            is_valid, errors = ExcelProcessor.validate_structure(df)
        except Exception as e:
            logger.error(f"Error a validar estructura: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Error al validar la estructra del archivo"
            )
        
        if not is_valid:
            if errors:
                raise HTTPException(status_code=400, detail={"errors": errors})
            else:
                raise HTTPException(
                    status_code=400,
                    detail="La estructura del archivo no es valida."
                )
        
        # Crear log de carga
        try:
            upload_log = ExcelUploadLog(
                filename=file.filename,
                status=UploadStatusEnum.PROCESSING,
                total_rows=len(df)
        )
            db.add(upload_log)
            db.commit()
            db.refresh(upload_log)
            
        except Exception as e:
            logger.error(f"Error al crear log de carga: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Error al iniciar el registro de carga"
            )
        
        #Procesae en backgroud - Converti Dataframe  a dict para serialización
        df_dict = df.to_dict('records')
        background_tasks.add_task(
            process_excel_data_safe,
            df_records=df_dict,
            upload_log_id=upload_log.id
        )
        
        return {
            "message": "Cerga iniciada existosamente",
            "upload_id": upload_log.id,
            "total_rows": len(df)
        }
        
    except HTTPException:
        raise 
    except Exception as e:
        logger.error(f"Error inisperaso al iniciar carga: {str(e)} ")
        
        #Intentar marcar del log como fallido si existe
        if upload_log and upload_log.id:
            try:
                upload_log.status = UploadStatusEnum.FAILED
                upload_log.error_message = str(e)
                db.commit()
            except Exception as db_error:
                logger.error(f"Error al actualizar log de fallo: {str(db_error)}")
                db.rollback()
        
        raise HTTPException(
            status_code=500,
            detail="Error inesperado al procesar el archivo"
            
        )

# ============================================
# NUEVO ENDPOINT: ESTADÍSTICAS
# ============================================
@router.get("/stats")
async def get_upload_stats(db: Session = Depends(get_db)):
    """
    Obtiene estadísticas de las cargas de Excel
    """
    try:
        logger.info("Obteniendo estadísticas de cargas...")
        
        # Estadísticas totales con validación
        try:
            total_uploads = db.query(func.count(ExcelUploadLog.id)).scalar()
            total_uploads = int(total_uploads) if total_uploads is not None else 0
        except Exception as e:
            logger.error(f"Error al obtener total de cargas: {str(e)}")
            total_uploads = 0
        
        try:
            total_successful = db.query(func.sum(ExcelUploadLog.successful_rows)).scalar()
            total_successful = int(total_successful) if total_successful is not None else 0
        except Exception as e:
            logger.error(f"Error al obtener filas exitosas: {str(e)}")
            total_successful = 0
        
        try:
            total_failed = db.query(func.sum(ExcelUploadLog.failed_rows)).scalar()
            total_failed = int(total_failed) if total_failed is not None else 0
        except Exception as e:
            logger.error(f"Error al obtener filas fallidas: {str(e)}")
            total_failed = 0
        
        logger.info(f"Total uploads: {total_uploads}, Exitosas: {total_successful}, Fallidas: {total_failed}")
        
        # Últimas 10 cargas para los gráficos
        recent_uploads = []
        try:
            recent_uploads = (
                db.query(ExcelUploadLog)
                .order_by(ExcelUploadLog.uploaded_at.desc())
                .limit(10)
                .all()
            )
        except Exception as e:
            logger.error(f"Error al obtener cargas recientes: {str(e)}")
        
        # Construir datos para gráficos
        chart_data = {
            'labels': [],
            'successful': [],
            'failed': [],
            'dates': []
        }
        
        if recent_uploads and len(recent_uploads) > 0:
            # Invertir para orden cronológico
            for upload in reversed(recent_uploads):
                try:
                    # Usar filename o un identificador
                    if upload.filename:
                        label = upload.filename
                    else:
                        label = f'Carga #{upload.id}'
                    
                    chart_data['labels'].append(label)
                    chart_data['successful'].append(upload.successful_rows if upload.successful_rows else 0)
                    chart_data['failed'].append(upload.failed_rows if upload.failed_rows else 0)
                    
                    # Formatear fecha
                    if upload.uploaded_at:
                        date_str = upload.uploaded_at.strftime('%Y-%m-%d')
                    else:
                        date_str = datetime.now().strftime('%Y-%m-%d')
                    
                    chart_data['dates'].append(date_str)
                except Exception as e:
                    logger.error(f"Error al procesar upload {upload.id}: {str(e)}")
                    continue
        
        logger.info(f"Datos de gráficos: {len(chart_data['labels'])} cargas")
        
        response = {
            'total_uploads': total_uploads,
            'total_successful': total_successful,
            'total_failed': total_failed,
            'chart_data': chart_data
        }
        
        logger.info(" Estadísticas obtenidas exitosamente")
        return response
        
    except Exception as e:
        logger.error(f"Error crítico al obtener estadísticas: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener estadísticas: {str(e)}"
        )


@router.get("/logs", response_model=List[UploadLogResponse])
async def get_upload_logs(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Obtiene el historial de cargas
    """
    try:
        if limit <= 0:
            limit = 50
        elif limit > 500:
            limit = 500
        
        logs = (
            db.query(ExcelUploadLog)
            .order_by(ExcelUploadLog.uploaded_at.desc())
            .limit(limit)
            .all()
        )
        
        if not logs:
            return []
        
        return logs
    
    except Exception as e:
        logger.error(f"Error al obtener logs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error al obtener el historial de cargas"
        )


@router.get("/logs/{upload_id}", response_model=UploadLogResponse)
async def get_upload_log(upload_id: int, db: Session = Depends(get_db)):
    """
    Obtiene el detalle de una carga específica
    """
    try:
        if upload_id <= 0:
            raise HTTPException(
                status_code=400,
                detail="ID de carga inválido"
            )
        
        log = db.query(ExcelUploadLog).filter(ExcelUploadLog.id == upload_id).first()
        
        if not log:
            raise HTTPException(
                status_code=404,
                detail=f"Log con ID {upload_id} no encontrado"
            )
        
        return log
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener log {upload_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error al obtener el detalle de la carga"
        )


def process_excel_data_safe(df_records: list, upload_log_id: int):
    """
    Versión segura de process_excel_data que crea su propia sesión de BD
    """
    from app.database import SessionLocal
    
    db = None
    try:
        # Crear nueva sesión de BD para el background task
        db = SessionLocal()
        
        if not db:
            logger.error("No se pudo crear sesión de base de datos")
            return
        
        # Convertir records de vuelta a DataFrame
        try:
            df = pd.DataFrame(df_records)
        except Exception as e:
            logger.error(f"Error al reconstruir DataFrame: {str(e)}")
            _mark_upload_as_failed(db, upload_log_id, "Error al procesar datos")
            return
        
        if df.empty:
            logger.error("DataFrame vacío en background task")
            _mark_upload_as_failed(db, upload_log_id, "No hay datos para procesar")
            return
        
        # Procesar datos
        process_excel_data(df, upload_log_id, db)
        
    except Exception as e:
        logger.error(f"Error crítico en background task: {str(e)}", exc_info=True)
        if db:
            try:
                _mark_upload_as_failed(db, upload_log_id, str(e))
            except Exception as mark_error:
                logger.error(f"Error al marcar carga como fallida: {str(mark_error)}")
    
    finally:
        if db:
            try:
                db.close()
            except Exception as e:
                logger.error(f"Error al cerrar sesión de BD: {str(e)}")


def _mark_upload_as_failed(db: Session, upload_log_id: int, error_message: str):
    """
    Función auxiliar para marcar una carga como fallida
    """
    try:
        upload_log = db.query(ExcelUploadLog).filter(
            ExcelUploadLog.id == upload_log_id
        ).first()
        
        if upload_log:
            upload_log.status = UploadStatusEnum.FAILED
            upload_log.error_message = error_message[:500]  # Limitar longitud
            db.commit()
        else:
            logger.error(f"No se encontró upload_log con ID {upload_log_id}")
    
    except Exception as e:
        logger.error(f"Error al marcar upload como fallido: {str(e)}")
        try:
            db.rollback()
        except:
            pass


def process_excel_data(df: pd.DataFrame, upload_log_id: int, db: Session):
    """
    Procesa los datos del Excel e inserta en la base de datos
    """
    successful = 0
    failed = 0
    total = len(df)
    
    try:
        # Validar datos iniciales
        if df is None or df.empty:
            raise ValueError("DataFrame vacío o None")
        
        if upload_log_id <= 0:
            raise ValueError("ID de upload_log inválido")
        
        logger.info(f"Iniciando procesamiento de {total} filas para upload_log {upload_log_id}")
        
        for idx, row in df.iterrows():
            try:
                # Validar fila
                row_dict = row.to_dict()
                
                if not row_dict:
                    logger.warning(f"Fila {idx + 2} vacía, saltando...")
                    failed += 1
                    continue
                
                try:
                    validated_row = ExcelProcessor.validate_row(row_dict, idx + 2)
                except Exception as e:
                    logger.error(f"Error al validar fila {idx + 2}: {str(e)}")
                    failed += 1
                    continue
                
                if not validated_row:
                    logger.warning(f"Fila {idx + 2}: validación retornó None")
                    failed += 1
                    continue
                
                if not validated_row.is_valid:
                    logger.warning(f"Fila {idx + 2}: datos inválidos")
                    failed += 1
                    continue
                
                # Validar que tenga los campos necesarios
                if not hasattr(validated_row, 'email') or not validated_row.email:
                    logger.warning(f"Fila {idx + 2}: email faltante")
                    failed += 1
                    continue
                
                if not hasattr(validated_row, 'name') or not validated_row.name:
                    logger.warning(f"Fila {idx + 2}: nombre faltante")
                    failed += 1
                    continue
                
                # Verificar si el email ya existe
                try:
                    existing_user = db.query(User).filter(
                        User.email == validated_row.email
                    ).first()
                except Exception as e:
                    logger.error(f"Error al consultar usuario existente: {str(e)}")
                    failed += 1
                    continue
                
                if existing_user:
                    logger.warning(f"Fila {idx + 2}: email {validated_row.email} ya existe")
                    failed += 1
                    continue
                
                # Crear nuevo usuario
                try:
                    new_user = User(
                        name=validated_row.name,
                        email=validated_row.email
                    )
                    db.add(new_user)
                    db.commit()
                    successful += 1
                    logger.info(f"Fila {idx + 2}: usuario creado exitosamente")
                
                except Exception as e:
                    logger.error(f"Error al crear usuario en fila {idx + 2}: {str(e)}")
                    failed += 1
                    try:
                        db.rollback()
                    except Exception as rollback_error:
                        logger.error(f"Error en rollback: {str(rollback_error)}")
                
            except Exception as row_error:
                logger.error(f"Error inesperado en fila {idx + 2}: {str(row_error)}")
                failed += 1
                try:
                    db.rollback()
                except:
                    pass
        
        # Actualizar log con resultados
        try:
            upload_log = db.query(ExcelUploadLog).filter(
                ExcelUploadLog.id == upload_log_id
            ).first()
            
            if upload_log:
                upload_log.status = UploadStatusEnum.COMPLETED
                upload_log.successful_rows = successful
                upload_log.failed_rows = failed
                db.commit()
                logger.info(f"Carga completada: {successful} exitosos, {failed} fallidos")
            else:
                logger.error(f"No se encontró upload_log con ID {upload_log_id} para actualizar")
        
        except Exception as e:
            logger.error(f"Error al actualizar log final: {str(e)}")
            try:
                db.rollback()
            except:
                pass
    
    except Exception as e:
        logger.error(f"Error crítico en procesamiento de Excel: {str(e)}", exc_info=True)
        
        # Intentar marcar como fallido
        try:
            upload_log = db.query(ExcelUploadLog).filter(
                ExcelUploadLog.id == upload_log_id
            ).first()
            
            if upload_log:
                upload_log.status = UploadStatusEnum.FAILED
                upload_log.error_message = str(e)[:500]
                upload_log.successful_rows = successful
                upload_log.failed_rows = failed
                db.commit()
        
        except Exception as update_error:
            logger.error(f"Error al actualizar log de fallo: {str(update_error)}")
            try:
                db.rollback()
            except:
                pass


async def process_excel_data_with_progress(
    df: pd.DataFrame, 
    upload_log_id: int, 
    db: Session,
    websocket_manager
):
    """
    Procesa los datos del Excel con WebSocket (versión mejorada)
    """
    successful = 0
    failed = 0
    total = len(df)
    
    try:
        if df is None or df.empty:
            raise ValueError("DataFrame vacío")
        
        if not websocket_manager:
            raise ValueError("WebSocket manager no disponible")
        
        for idx, row in df.iterrows():
            try:
                # Validar fila
                validated_row = ExcelProcessor.validate_row(row.to_dict(), idx + 2)
                
                if not validated_row or not validated_row.is_valid:
                    failed += 1
                else:
                    # Verificar duplicados
                    existing_user = db.query(User).filter(
                        User.email == validated_row.email
                    ).first()
                    
                    if existing_user:
                        failed += 1
                    else:
                        # Crear usuario
                        new_user = User(
                            name=validated_row.name,
                            email=validated_row.email
                        )
                        db.add(new_user)
                        db.commit()
                        successful += 1
                
                # Enviar progreso
                current = idx + 1
                percentage = (current / total) * 100
                
                try:
                    await websocket_manager.send_progress({
                        "current": current,
                        "total": total,
                        "percentage": round(percentage, 2),
                        "successful": successful,
                        "failed": failed,
                        "status": "processing"
                    })
                except Exception as ws_error:
                    logger.error(f"Error al enviar progreso por WebSocket: {str(ws_error)}")
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error en fila {idx + 2}: {str(e)}")
                failed += 1
                try:
                    db.rollback()
                except:
                    pass
        
        # Actualizar log final
        try:
            upload_log = db.query(ExcelUploadLog).filter(
                ExcelUploadLog.id == upload_log_id
            ).first()
            
            if upload_log:
                upload_log.status = UploadStatusEnum.COMPLETED
                upload_log.successful_rows = successful
                upload_log.failed_rows = failed
                db.commit()
        except Exception as e:
            logger.error(f"Error al actualizar log: {str(e)}")
        
        # Enviar progreso final
        try:
            await websocket_manager.send_progress({
                "current": total,
                "total": total,
                "percentage": 100,
                "successful": successful,
                "failed": failed,
                "status": "completed"
            })
        except Exception as ws_error:
            logger.error(f"Error al enviar progreso final: {str(ws_error)}")
        
        logger.info(f"Carga completada: {successful} exitosos, {failed} fallidos")
    
    except Exception as e:
        logger.error(f"Error crítico: {str(e)}", exc_info=True)
        
        try:
            upload_log = db.query(ExcelUploadLog).filter(
                ExcelUploadLog.id == upload_log_id
            ).first()
            
            if upload_log:
                upload_log.status = UploadStatusEnum.FAILED
                upload_log.error_message = str(e)
                db.commit()
        except:
            pass
        
        try:
            await websocket_manager.send_progress({
                "status": "failed",
                "error": str(e)
            })
        except:
            pass